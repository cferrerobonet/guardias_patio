"""
Sistema de caché de soluciones de guardias.
Guarda soluciones exitosas y las reutiliza cuando la configuración es similar.
"""
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from models.models import Configuracion, Guardia, Profesor
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ConfiguracionHash:
    """Representa un hash de configuración para comparación."""
    num_profesores_activos: int
    num_dias_lectivos: int
    num_recreos: int
    num_zonas: int
    turnos_disponibles: List[str]
    zonas_disponibles: List[str]
    fecha_inicio: str
    fecha_fin: str
    hash_profesores: str  # Hash de profesores y sus características
    hash_completo: str  # Hash SHA256 de toda la configuración


@dataclass
class SolucionCacheada:
    """Solución guardada en caché."""
    id_cache: str
    fecha_creacion: datetime
    config_hash: ConfiguracionHash
    guardias: List[Dict]  # Lista de guardias serializadas
    estadisticas: Dict
    estrategia_usada: str
    tiempo_generacion: float
    similitud_requerida: float = 0.95  # Similitud mínima para reutilizar


class CacheSolucionesGuardias:
    """
    Sistema de caché que guarda y recupera soluciones de guardias.
    """

    def __init__(self, db: Session, cache_dir: Optional[Path] = None):
        self.db = db
        self.cache_dir = cache_dir or Path("data/cache_guardias")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def calcular_hash_configuracion(
        self,
        config: Configuracion,
        dias_lectivos: List[date]
    ) -> ConfiguracionHash:
        """
        Calcula hash único de la configuración actual.
        """
        # Obtener profesores activos
        profesores = self.db.query(Profesor).filter(Profesor.activo.is_(True)).all()

        # Datos básicos
        num_profesores = len(profesores)
        num_dias = len(dias_lectivos)
        num_recreos = len(config.recreos)
        num_zonas = len(config.zonas)

        # Turnos únicos
        turnos_unicos = sorted(set(r.turno for r in config.recreos))

        # Zonas únicas
        zonas_unicas = sorted([z.nombre for z in config.zonas])

        # Hash de profesores (características relevantes)
        profesores_data = []
        for prof in sorted(profesores, key=lambda p: p.id):
            prof_data = {
                'turno': prof.turno,  # turno es string, no array
                'zona_preferida_id': prof.zona_preferida_id,  # ID de zona preferida (no lista)
                'horas_contrato': prof.horas_contrato,
                'tutor': prof.tutor,
                'num_ausencias': 0  # TODO: implementar conteo de ausencias si es necesario
            }
            profesores_data.append(prof_data)

        hash_profesores = hashlib.sha256(
            json.dumps(profesores_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Hash completo
        config_completa = {
            'num_profesores': num_profesores,
            'num_dias': num_dias,
            'num_recreos': num_recreos,
            'num_zonas': num_zonas,
            'turnos': turnos_unicos,
            'zonas': zonas_unicas,
            'fecha_inicio': config.fecha_inicio_curso.isoformat(),
            'fecha_fin': config.fecha_fin_curso.isoformat(),
            'profesores': profesores_data
        }

        hash_completo = hashlib.sha256(
            json.dumps(config_completa, sort_keys=True).encode()
        ).hexdigest()

        return ConfiguracionHash(
            num_profesores_activos=num_profesores,
            num_dias_lectivos=num_dias,
            num_recreos=num_recreos,
            num_zonas=num_zonas,
            turnos_disponibles=turnos_unicos,
            zonas_disponibles=zonas_unicas,
            fecha_inicio=config.fecha_inicio_curso.isoformat(),
            fecha_fin=config.fecha_fin_curso.isoformat(),
            hash_profesores=hash_profesores,
            hash_completo=hash_completo
        )

    def guardar_solucion(
        self,
        guardias: List[Guardia],
        config: Configuracion,
        dias_lectivos: List[date],
        estadisticas: Dict,
        estrategia: str,
        tiempo_generacion: float
    ) -> str:
        """
        Guarda una solución exitosa en caché.

        Returns:
            ID del caché guardado
        """
        # Calcular hash
        config_hash = self.calcular_hash_configuracion(config, dias_lectivos)

        # Serializar guardias
        guardias_data = []
        for guardia in guardias:
            guardias_data.append({
                'profesor_id': guardia.profesor_id,
                'fecha': guardia.fecha.isoformat(),
                'recreo': guardia.recreo,
                'zona': guardia.zona,
                'turno': guardia.turno
            })

        # Crear solución
        solucion = SolucionCacheada(
            id_cache=config_hash.hash_completo[:16],
            fecha_creacion=datetime.now(),
            config_hash=config_hash,
            guardias=guardias_data,
            estadisticas=estadisticas,
            estrategia_usada=estrategia,
            tiempo_generacion=tiempo_generacion
        )

        # Guardar en archivo
        cache_file = self.cache_dir / f"{solucion.id_cache}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(solucion), f, indent=2, default=str)

        logger.info(f"✅ Solución guardada en caché: {solucion.id_cache}")
        logger.info(f"   Guardias: {len(guardias)}")
        logger.info(f"   Estrategia: {estrategia}")

        return solucion.id_cache

    def buscar_solucion_similar(
        self,
        config: Configuracion,
        dias_lectivos: List[date],
        umbral_similitud: float = 0.90
    ) -> Optional[SolucionCacheada]:
        """
        Busca una solución cacheada similar a la configuración actual.

        Args:
            umbral_similitud: Similitud mínima requerida (0.0-1.0)

        Returns:
            SolucionCacheada si encuentra una similar, None si no
        """
        config_hash_actual = self.calcular_hash_configuracion(config, dias_lectivos)

        # Verificar si hay match exacto
        cache_exacto = self.cache_dir / f"{config_hash_actual.hash_completo[:16]}.json"
        if cache_exacto.exists():
            logger.info("🎯 Encontrada solución EXACTA en caché")
            return self._cargar_solucion_desde_archivo(cache_exacto)

        # Buscar soluciones similares
        logger.info(f"🔍 Buscando soluciones similares (umbral: {umbral_similitud*100:.0f}%)...")

        mejores_candidatos = []

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                solucion = self._cargar_solucion_desde_archivo(cache_file)
                similitud = self._calcular_similitud(
                    config_hash_actual,
                    solucion.config_hash
                )

                if similitud >= umbral_similitud:
                    mejores_candidatos.append((similitud, solucion))
                    logger.info(
                        f"   Candidato encontrado: {solucion.id_cache} "
                        f"(similitud: {similitud*100:.1f}%)"
                    )

            except Exception as e:
                logger.warning(f"Error al leer caché {cache_file}: {e}")
                continue

        if mejores_candidatos:
            # Ordenar por similitud y tomar el mejor
            mejores_candidatos.sort(key=lambda x: x[0], reverse=True)
            mejor_similitud, mejor_solucion = mejores_candidatos[0]

            logger.info(
                f"✅ Solución similar encontrada: {mejor_solucion.id_cache} "
                f"(similitud: {mejor_similitud*100:.1f}%)"
            )
            return mejor_solucion

        logger.info("❌ No se encontraron soluciones similares en caché")
        return None

    def _calcular_similitud(
        self,
        hash1: ConfiguracionHash,
        hash2: ConfiguracionHash
    ) -> float:
        """
        Calcula similitud entre dos configuraciones (0.0-1.0).
        """
        puntos = 0
        total = 0

        # Comparar características numéricas (peso: 40%)
        caracteristicas = [
            ('num_profesores_activos', 10),
            ('num_dias_lectivos', 10),
            ('num_recreos', 10),
            ('num_zonas', 10),
        ]

        for campo, peso in caracteristicas:
            val1 = getattr(hash1, campo)
            val2 = getattr(hash2, campo)

            if val1 == val2:
                puntos += peso
            else:
                # Penalizar según diferencia porcentual
                diff = abs(val1 - val2) / max(val1, val2)
                puntos += peso * max(0, 1 - diff)

            total += peso

        # Comparar turnos (peso: 20%)
        turnos1 = set(hash1.turnos_disponibles)
        turnos2 = set(hash2.turnos_disponibles)
        if turnos1 and turnos2:
            similitud_turnos = len(turnos1 & turnos2) / len(turnos1 | turnos2)
            puntos += 20 * similitud_turnos
        total += 20

        # Comparar zonas (peso: 20%)
        zonas1 = set(hash1.zonas_disponibles)
        zonas2 = set(hash2.zonas_disponibles)
        if zonas1 and zonas2:
            similitud_zonas = len(zonas1 & zonas2) / len(zonas1 | zonas2)
            puntos += 20 * similitud_zonas
        total += 20

        # Comparar hash de profesores (peso: 20%)
        if hash1.hash_profesores == hash2.hash_profesores:
            puntos += 20
        total += 20

        return puntos / total if total > 0 else 0.0

    def _cargar_solucion_desde_archivo(self, archivo: Path) -> SolucionCacheada:
        """Carga una solución desde archivo JSON."""
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruir objetos de dataclass
        return SolucionCacheada(
            id_cache=data['id_cache'],
            fecha_creacion=datetime.fromisoformat(data['fecha_creacion']),
            config_hash=ConfiguracionHash(**data['config_hash']),
            guardias=data['guardias'],
            estadisticas=data['estadisticas'],
            estrategia_usada=data['estrategia_usada'],
            tiempo_generacion=data['tiempo_generacion']
        )

    def aplicar_solucion_cacheada(
        self,
        solucion: SolucionCacheada
    ) -> List[Guardia]:
        """
        Convierte una solución cacheada en objetos Guardia.
        """
        guardias = []

        for guardia_data in solucion.guardias:
            guardia = Guardia(
                profesor_id=guardia_data['profesor_id'],
                fecha=date.fromisoformat(guardia_data['fecha']),
                recreo=guardia_data['recreo'],
                zona=guardia_data['zona'],
                turno=guardia_data['turno']
            )
            guardias.append(guardia)

        logger.info(f"✅ Aplicada solución desde caché: {len(guardias)} guardias")
        return guardias

    def limpiar_cache_antiguo(self, dias_max: int = 30):
        """
        Elimina soluciones del caché más antiguas que X días.
        """
        fecha_limite = datetime.now().timestamp() - (dias_max * 24 * 60 * 60)
        eliminados = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                solucion = self._cargar_solucion_desde_archivo(cache_file)
                if solucion.fecha_creacion.timestamp() < fecha_limite:
                    cache_file.unlink()
                    eliminados += 1
            except Exception:
                continue

        if eliminados > 0:
            logger.info(f"🗑️  Limpieza de caché: {eliminados} soluciones antiguas eliminadas")

        return eliminados

    def obtener_estadisticas_cache(self) -> Dict:
        """Obtiene estadísticas del caché actual."""
        cache_files = list(self.cache_dir.glob("*.json"))

        if not cache_files:
            return {
                'total_soluciones': 0,
                'espacio_usado_mb': 0,
                'solucion_mas_reciente': None,
                'solucion_mas_antigua': None
            }

        # Calcular tamaño
        espacio_bytes = sum(f.stat().st_size for f in cache_files)

        # Fechas
        fechas = []
        for cache_file in cache_files:
            try:
                solucion = self._cargar_solucion_desde_archivo(cache_file)
                fechas.append(solucion.fecha_creacion)
            except Exception:
                continue

        return {
            'total_soluciones': len(cache_files),
            'espacio_usado_mb': espacio_bytes / (1024 * 1024),
            'solucion_mas_reciente': max(fechas).isoformat() if fechas else None,
            'solucion_mas_antigua': min(fechas).isoformat() if fechas else None
        }
