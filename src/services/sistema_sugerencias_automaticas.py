"""
Sistema de sugerencias automáticas que aplica correcciones inteligentes
basadas en el diagnóstico de problemas.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from models.models import Configuracion, Profesor
from services.validators import TurnoValidator
from sqlalchemy.orm import Session

from src.services.diagnosticador_guardias import DiagnosticoCompleto, ProblemaDetectado

logger = logging.getLogger(__name__)

# Instancia del validador de turnos
_turno_validator = TurnoValidator()


@dataclass
class CambioSugerido:
    """Representa un cambio sugerido en la configuración."""
    tipo: str  # 'activar_profesor', 'agregar_zona', 'reducir_recreo', etc.
    descripcion: str
    impacto_estimado: str  # 'ALTO', 'MEDIO', 'BAJO'
    detalles: Dict
    revertible: bool = True


@dataclass
class PaqueteCambios:
    """Conjunto de cambios sugeridos que se aplican juntos."""
    titulo: str
    cambios: List[CambioSugerido]
    problema_objetivo: str
    mejora_esperada: str


class SistemaSugerenciasAutomaticas:
    """
    Analiza diagnósticos y genera cambios automáticos en la configuración
    para resolver problemas detectados.
    """

    def __init__(self, db: Session, config: Configuracion):
        self.db = db
        self.config = config

    def generar_paquetes_sugerencias(
        self,
        diagnostico: DiagnosticoCompleto
    ) -> List[PaqueteCambios]:
        """
        Genera paquetes de cambios sugeridos basados en el diagnóstico.
        """
        paquetes = []

        # 1. Resolver profesores sin guardias
        for problema in diagnostico.problemas_criticos:
            if problema.tipo == 'profesor_sin_guardias':
                paquete = self._generar_sugerencias_profesores_sin_guardias(problema)
                if paquete:
                    paquetes.append(paquete)

            elif problema.tipo == 'slots_vacios':
                paquete = self._generar_sugerencias_slots_vacios(problema)
                if paquete:
                    paquetes.append(paquete)

        # 2. Resolver problemas de fechas de inicio
        for problema in diagnostico.problemas_altos:
            if problema.tipo == 'fecha_inicio_incumplida':
                paquete = self._generar_sugerencias_fechas_inicio(problema)
                if paquete:
                    paquetes.append(paquete)

            elif problema.tipo == 'cuota_incompleta':
                paquete = self._generar_sugerencias_cuotas_incompletas(problema)
                if paquete:
                    paquetes.append(paquete)

        return paquetes

    def _generar_sugerencias_profesores_sin_guardias(
        self,
        problema: ProblemaDetectado
    ) -> Optional[PaqueteCambios]:
        """Genera sugerencias para resolver profesores sin guardias."""
        cambios = []
        turno = problema.detalles.get('turno', 'desconocido')
        causas = problema.detalles.get('causas', {})

        # Opción 1: Activar profesores inactivos del mismo turno
        profesores_inactivos = self.db.query(Profesor).filter(
            Profesor.activo.is_(False)
        ).all()

        candidatos = [
            p for p in profesores_inactivos
            if _turno_validator.es_compatible(p.turno, turno)
        ]

        if candidatos:
            for prof in candidatos[:3]:  # Máximo 3
                cambios.append(CambioSugerido(
                    tipo='activar_profesor',
                    descripcion=f"Activar profesor '{prof.nombre_completo}' (turno {turno})",
                    impacto_estimado='ALTO',
                    detalles={
                        'profesor_id': prof.id,
                        'profesor_nombre': prof.nombre_completo,
                        'turno': prof.turno,
                        'zona_preferida': prof.zona_preferida.nombre_zona if prof.zona_preferida else 'Todas'
                    }
                ))

        # Opción 2: Ampliar turnos de profesores existentes
        profesores_otros_turnos = self.db.query(Profesor).filter(
            Profesor.activo.is_(True)
        ).all()

        candidatos_ampliar = [
            p for p in profesores_otros_turnos
            if not _turno_validator.es_compatible(p.turno, turno)
        ]

        if candidatos_ampliar:
            for prof in candidatos_ampliar[:2]:
                cambios.append(CambioSugerido(
                    tipo='ampliar_turno_profesor',
                    descripcion=f"Ampliar turnos de '{prof.nombre}' para incluir '{turno}'",
                    impacto_estimado='MEDIO',
                    detalles={
                        'profesor_id': prof.id,
                        'profesor_nombre': prof.nombre,
                        'turnos_actuales': prof.turnos or [],
                        'turno_nuevo': turno
                    }
                ))

        # Opción 3: Si hay slots insuficientes, reducir recreos
        if causas.get('slots_insuficientes'):
            recreos_turno = [r for r in self.config.recreos if r.turno == turno]
            if len(recreos_turno) > 1:
                cambios.append(CambioSugerido(
                    tipo='reducir_recreos',
                    descripcion=f"Reducir recreos en turno '{turno}' de {len(recreos_turno)} a {len(recreos_turno)-1}",
                    impacto_estimado='ALTO',
                    detalles={
                        'turno': turno,
                        'recreos_actuales': len(recreos_turno),
                        'recreos_propuestos': len(recreos_turno) - 1,
                        'recreo_eliminar': recreos_turno[-1].numero
                    }
                ))

        if not cambios:
            return None

        return PaqueteCambios(
            titulo=f"Resolver profesores sin guardias en turno '{turno}'",
            cambios=cambios,
            problema_objetivo=problema.descripcion,
            mejora_esperada=f"Asegurar que todos los profesores de turno '{turno}' tengan guardias"
        )

    def _generar_sugerencias_slots_vacios(
        self,
        problema: ProblemaDetectado
    ) -> Optional[PaqueteCambios]:
        """Genera sugerencias para cubrir slots vacíos."""
        cambios = []
        huecos_turno = problema.detalles.get('huecos_por_turno', {})
        huecos_zona = problema.detalles.get('huecos_por_zona', {})

        # Identificar turno/zona más problemáticos
        if huecos_turno:
            turno_peor = max(huecos_turno.items(), key=lambda x: x[1])
            turno, num_huecos = turno_peor

            # Sugerir activar profesores para ese turno
            profesores_inactivos = self.db.query(Profesor).filter(
                Profesor.activo.is_(False)
            ).all()

            candidatos = [
                p for p in profesores_inactivos
                if turno in (p.turnos or ['mañana'])
            ][:3]

            for prof in candidatos:
                cambios.append(CambioSugerido(
                    tipo='activar_profesor',
                    descripcion=f"Activar '{prof.nombre}' para cubrir slots en turno '{turno}'",
                    impacto_estimado='ALTO',
                    detalles={
                        'profesor_id': prof.id,
                        'profesor_nombre': prof.nombre,
                        'turno_objetivo': turno,
                        'huecos_a_cubrir': num_huecos
                    }
                ))

        if huecos_zona:
            zona_peor = max(huecos_zona.items(), key=lambda x: x[1])
            zona_nombre, num_huecos = zona_peor

            # Buscar zona en configuración
            zona_obj = next((z for z in self.config.zonas if z.nombre == zona_nombre), None)

            if zona_obj:
                # Sugerir asignar más profesores a esa zona
                profesores_sin_zona = self.db.query(Profesor).filter(
                    Profesor.activo.is_(True)
                ).all()

                candidatos = [
                    p for p in profesores_sin_zona
                    if not p.zonas or zona_obj.id not in [z.id for z in p.zonas]
                ][:3]

                for prof in candidatos:
                    cambios.append(CambioSugerido(
                        tipo='asignar_zona_profesor',
                        descripcion=f"Asignar zona '{zona_nombre}' a profesor '{prof.nombre}'",
                        impacto_estimado='MEDIO',
                        detalles={
                            'profesor_id': prof.id,
                            'profesor_nombre': prof.nombre,
                            'zona_id': zona_obj.id,
                            'zona_nombre': zona_nombre,
                            'huecos_a_cubrir': num_huecos
                        }
                    ))

        if not cambios:
            return None

        return PaqueteCambios(
            titulo="Cubrir slots vacíos",
            cambios=cambios,
            problema_objetivo=problema.descripcion,
            mejora_esperada="Aumentar cobertura hacia 100%"
        )

    def _generar_sugerencias_fechas_inicio(
        self,
        problema: ProblemaDetectado
    ) -> Optional[PaqueteCambios]:
        """Genera sugerencias para mejorar cumplimiento de fechas de inicio."""
        cambios = []

        profesores_retrasados = problema.detalles.get('profesores_retrasados', [])

        # Para cada profesor retrasado, revisar ausencias tempranas
        for prof_data in profesores_retrasados[:5]:  # Máximo 5
            cambios.append(CambioSugerido(
                tipo='revisar_ausencias_tempranas',
                descripcion=(
                    f"Revisar ausencias de '{prof_data['nombre']}' "
                    f"en primeras semanas (retraso: {prof_data['dias_retraso']} días)"
                ),
                impacto_estimado='MEDIO',
                detalles={
                    'profesor_nombre': prof_data['nombre'],
                    'fecha_inicio_esperada': prof_data['fecha_inicio'],
                    'primera_guardia': prof_data['primera_guardia'],
                    'dias_retraso': prof_data['dias_retraso']
                }
            ))

        if not cambios:
            return None

        return PaqueteCambios(
            titulo="Mejorar cumplimiento de fechas de inicio",
            cambios=cambios,
            problema_objetivo=problema.descripcion,
            mejora_esperada="Reducir retraso promedio en fechas de inicio"
        )

    def _generar_sugerencias_cuotas_incompletas(
        self,
        problema: ProblemaDetectado
    ) -> Optional[PaqueteCambios]:
        """Genera sugerencias para resolver cuotas incompletas."""
        cambios = []

        profesores_deficit = problema.detalles.get('profesores', [])

        for prof_data in profesores_deficit[:5]:
            cambios.append(CambioSugerido(
                tipo='revisar_disponibilidad_profesor',
                descripcion=(
                    f"Revisar disponibilidad de '{prof_data['nombre']}' "
                    f"(déficit: {prof_data['deficit']} guardias, {prof_data['deficit_porcentaje']:.0f}%)"
                ),
                impacto_estimado='MEDIO',
                detalles={
                    'profesor_nombre': prof_data['nombre'],
                    'esperadas': prof_data['esperadas'],
                    'asignadas': prof_data['asignadas'],
                    'deficit': prof_data['deficit']
                }
            ))

        if not cambios:
            return None

        return PaqueteCambios(
            titulo="Resolver cuotas incompletas",
            cambios=cambios,
            problema_objetivo=problema.descripcion,
            mejora_esperada="Balancear distribución de guardias entre profesores"
        )

    def aplicar_cambios(
        self,
        paquete: PaqueteCambios,
        cambios_seleccionados: Optional[List[int]] = None
    ) -> Dict:
        """
        Aplica los cambios seleccionados del paquete.

        Args:
            paquete: Paquete de cambios
            cambios_seleccionados: Índices de cambios a aplicar (None = todos)

        Returns:
            Diccionario con resultados de la aplicación
        """
        if cambios_seleccionados is None:
            cambios_a_aplicar = paquete.cambios
        else:
            cambios_a_aplicar = [paquete.cambios[i] for i in cambios_seleccionados]

        resultados = {
            'aplicados': 0,
            'fallidos': 0,
            'detalles': []
        }

        for cambio in cambios_a_aplicar:
            try:
                resultado = self._aplicar_cambio_individual(cambio)
                resultados['aplicados'] += 1
                resultados['detalles'].append({
                    'cambio': cambio.descripcion,
                    'exitoso': True,
                    'resultado': resultado
                })
            except Exception as e:
                resultados['fallidos'] += 1
                resultados['detalles'].append({
                    'cambio': cambio.descripcion,
                    'exitoso': False,
                    'error': str(e)
                })
                logger.error(f"Error al aplicar cambio: {cambio.descripcion} - {e}")

        return resultados

    def _aplicar_cambio_individual(self, cambio: CambioSugerido) -> str:
        """Aplica un cambio individual según su tipo."""

        if cambio.tipo == 'activar_profesor':
            profesor_id = cambio.detalles['profesor_id']
            profesor = self.db.query(Profesor).get(profesor_id)
            if profesor:
                profesor.activo = True
                self.db.commit()
                return f"Profesor activado: {profesor.nombre}"

        elif cambio.tipo == 'ampliar_turno_profesor':
            profesor_id = cambio.detalles['profesor_id']
            turno_nuevo = cambio.detalles['turno_nuevo']
            profesor = self.db.query(Profesor).get(profesor_id)
            if profesor:
                turnos_actuales = profesor.turnos or []
                if turno_nuevo not in turnos_actuales:
                    profesor.turnos = turnos_actuales + [turno_nuevo]
                    self.db.commit()
                return f"Turno '{turno_nuevo}' añadido a {profesor.nombre}"

        elif cambio.tipo == 'asignar_zona_profesor':
            profesor_id = cambio.detalles['profesor_id']
            zona_id = cambio.detalles['zona_id']
            profesor = self.db.query(Profesor).get(profesor_id)
            zona = next((z for z in self.config.zonas if z.id == zona_id), None)

            if profesor and zona:
                # Los profesores pueden trabajar en TODAS las zonas (no hay restricción)
                # Solo tienen zona_preferida_id como preferencia suave
                # Actualizar la zona preferida
                profesor.zona_preferida_id = zona.id
                self.db.commit()
                return f"Zona preferida '{zona.nombre_zona}' actualizada para {profesor.nombre_completo}"

        elif cambio.tipo == 'reducir_recreos':
            recreo_eliminar = cambio.detalles['recreo_eliminar']
            recreos_nuevos = [r for r in self.config.recreos if r.numero != recreo_eliminar]
            self.config.recreos = recreos_nuevos
            self.db.commit()
            return f"Recreo {recreo_eliminar} eliminado"

        elif cambio.tipo in ['revisar_ausencias_tempranas', 'revisar_disponibilidad_profesor']:
            # Estos requieren intervención manual
            return "Revisión manual requerida"

        return "Cambio aplicado"
