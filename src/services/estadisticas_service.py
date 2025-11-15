"""
EstadisticasService - Cálculos estadísticos centralizados

Responsabilidad: Calcular todas las métricas y estadísticas
relacionadas con la asignación de guardias de forma consistente.
"""

from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional, Tuple

from models.models import Guardia, Profesor
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


class EstadisticasService:
    """
    Servicio centralizado para cálculos estadísticos.
    
    Elimina duplicación de lógica de estadísticas en múltiples archivos.
    """

    def __init__(self, session: Session):
        self.session = session

    def calcular_guardias_por_profesor(
        self, guardias: List[Guardia]
    ) -> Dict[int, int]:
        """
        Cuenta guardias asignadas por profesor.

        Args:
            guardias: Lista de guardias

        Returns:
            Dict {profesor_id: num_guardias}
        """
        contador = defaultdict(int)
        for guardia in guardias:
            contador[guardia.profesor_id] += 1
        return dict(contador)

    def calcular_cobertura(
        self, guardias_asignadas: int, total_slots: int
    ) -> float:
        """
        Calcula porcentaje de cobertura.

        Args:
            guardias_asignadas: Número de guardias asignadas
            total_slots: Total de slots disponibles

        Returns:
            Porcentaje de cobertura (0.0 a 1.0)
        """
        if total_slots == 0:
            return 0.0
        return guardias_asignadas / total_slots

    def calcular_participacion(
        self, guardias: List[Guardia], total_profesores: int
    ) -> float:
        """
        Calcula porcentaje de profesores participantes.

        Args:
            guardias: Lista de guardias
            total_profesores: Total de profesores disponibles

        Returns:
            Porcentaje de participación (0.0 a 1.0)
        """
        if total_profesores == 0:
            return 0.0

        profesores_con_guardias = len(
            set(g.profesor_id for g in guardias)
        )
        return profesores_con_guardias / total_profesores

    def calcular_promedio_guardias(
        self, guardias: List[Guardia]
    ) -> float:
        """
        Calcula promedio de guardias por profesor participante.

        Args:
            guardias: Lista de guardias

        Returns:
            Promedio de guardias
        """
        if not guardias:
            return 0.0

        profesores_unicos = len(set(g.profesor_id for g in guardias))
        if profesores_unicos == 0:
            return 0.0

        return len(guardias) / profesores_unicos

    def calcular_desviacion_cuotas(
        self,
        guardias: List[Guardia],
        cuotas: Dict[int, int],
    ) -> Tuple[float, float]:
        """
        Calcula desviación promedio y máxima respecto a cuotas.

        Args:
            guardias: Lista de guardias
            cuotas: Dict {profesor_id: cuota_objetivo}

        Returns:
            Tupla (desviacion_promedio, desviacion_maxima)
        """
        if not cuotas:
            return 0.0, 0.0

        asignadas = self.calcular_guardias_por_profesor(guardias)

        desviaciones = []
        for profesor_id, cuota in cuotas.items():
            if cuota == 0:
                continue

            guardias_asignadas = asignadas.get(profesor_id, 0)
            desviacion = abs(guardias_asignadas - cuota) / cuota
            desviaciones.append(desviacion)

        if not desviaciones:
            return 0.0, 0.0

        promedio = sum(desviaciones) / len(desviaciones)
        maxima = max(desviaciones)

        return promedio, maxima

    def calcular_balance(
        self, guardias: List[Guardia]
    ) -> float:
        """
        Calcula coeficiente de variación de la distribución.

        Args:
            guardias: Lista de guardias

        Returns:
            Coeficiente de variación (menor = más equitativo)
        """
        if not guardias:
            return 0.0

        contador = self.calcular_guardias_por_profesor(guardias)
        valores = list(contador.values())

        if not valores or len(valores) < 2:
            return 0.0

        promedio = sum(valores) / len(valores)
        if promedio == 0:
            return 0.0

        # Desviación estándar
        varianza = sum((x - promedio) ** 2 for x in valores) / len(valores)
        desviacion = varianza ** 0.5

        # Coeficiente de variación
        return desviacion / promedio

    def identificar_profesores_sin_guardias(
        self,
        guardias: List[Guardia],
        profesores: List[Profesor],
    ) -> List[Profesor]:
        """
        Identifica profesores activos sin guardias asignadas.

        Args:
            guardias: Lista de guardias
            profesores: Lista de profesores

        Returns:
            Lista de profesores sin guardias
        """
        ids_con_guardias = set(g.profesor_id for g in guardias)
        return [
            p for p in profesores
            if p.activo and p.id not in ids_con_guardias
        ]

    def calcular_guardias_por_fecha(
        self, guardias: List[Guardia]
    ) -> Dict[date, int]:
        """
        Cuenta guardias por fecha.

        Args:
            guardias: Lista de guardias

        Returns:
            Dict {fecha: num_guardias}
        """
        contador = defaultdict(int)
        for guardia in guardias:
            contador[guardia.fecha] += 1
        return dict(contador)

    def calcular_guardias_por_zona(
        self, guardias: List[Guardia]
    ) -> Dict[int, int]:
        """
        Cuenta guardias por zona.

        Args:
            guardias: Lista de guardias

        Returns:
            Dict {zona_id: num_guardias}
        """
        contador = defaultdict(int)
        for guardia in guardias:
            if guardia.zona_id:
                contador[guardia.zona_id] += 1
        return dict(contador)

    def detectar_profesores_con_multiples_guardias_mismo_dia(
        self, guardias: List[Guardia]
    ) -> List[Tuple[int, date, int]]:
        """
        Detecta profesores con más de una guardia el mismo día.

        Args:
            guardias: Lista de guardias

        Returns:
            Lista de tuplas (profesor_id, fecha, num_guardias)
        """
        contador: Dict[Tuple[int, date], int] = defaultdict(int)

        for guardia in guardias:
            key = (guardia.profesor_id, guardia.fecha)
            contador[key] += 1

        # Filtrar solo los que tienen más de 1
        conflictos = [
            (profesor_id, fecha, count)
            for (profesor_id, fecha), count in contador.items()
            if count > 1
        ]

        return conflictos

    def generar_resumen_completo(
        self,
        guardias: List[Guardia],
        profesores: List[Profesor],
        cuotas: Optional[Dict[int, int]] = None,
        total_slots: Optional[int] = None,
    ) -> Dict:
        """
        Genera resumen estadístico completo.

        Args:
            guardias: Lista de guardias
            profesores: Lista de profesores
            cuotas: Cuotas objetivo (opcional)
            total_slots: Total de slots (opcional)

        Returns:
            Dict con todas las métricas
        """
        guardias_por_prof = self.calcular_guardias_por_profesor(guardias)
        sin_guardias = self.identificar_profesores_sin_guardias(
            guardias, profesores
        )
        conflictos = self.detectar_profesores_con_multiples_guardias_mismo_dia(
            guardias
        )

        resumen = {
            "total_guardias": len(guardias),
            "profesores_con_guardias": len(guardias_por_prof),
            "profesores_sin_guardias": len(sin_guardias),
            "total_profesores": len([p for p in profesores if p.activo]),
            "promedio_guardias": self.calcular_promedio_guardias(guardias),
            "balance": self.calcular_balance(guardias),
            "conflictos_mismo_dia": len(conflictos),
        }

        # Métricas de min/max
        if guardias_por_prof:
            resumen["min_guardias"] = min(guardias_por_prof.values())
            resumen["max_guardias"] = max(guardias_por_prof.values())
        else:
            resumen["min_guardias"] = 0
            resumen["max_guardias"] = 0

        # Cobertura si se proporciona total_slots
        if total_slots is not None:
            resumen["cobertura"] = self.calcular_cobertura(
                len(guardias), total_slots
            )
            resumen["cobertura_porcentaje"] = resumen["cobertura"] * 100

        # Participación
        total_activos = len([p for p in profesores if p.activo])
        if total_activos > 0:
            resumen["participacion"] = self.calcular_participacion(
                guardias, total_activos
            )
            resumen["participacion_porcentaje"] = (
                resumen["participacion"] * 100
            )

        # Desviación de cuotas si se proporcionan
        if cuotas:
            desv_prom, desv_max = self.calcular_desviacion_cuotas(
                guardias, cuotas
            )
            resumen["desviacion_promedio"] = desv_prom
            resumen["desviacion_maxima"] = desv_max

        # Distribución por fecha y zona
        resumen["guardias_por_fecha"] = self.calcular_guardias_por_fecha(
            guardias
        )
        resumen["guardias_por_zona"] = self.calcular_guardias_por_zona(
            guardias
        )

        return resumen

    def log_resumen(self, resumen: Dict) -> None:
        """
        Imprime resumen en logs de forma formateada.

        Args:
            resumen: Dict con métricas
        """
        logger.info("═" * 60)
        logger.info("RESUMEN DE ASIGNACIÓN")
        logger.info("═" * 60)

        logger.info(
            f"📊 Total guardias: {resumen['total_guardias']}"
        )
        logger.info(
            f"👥 Profesores participantes: "
            f"{resumen['profesores_con_guardias']}/{resumen['total_profesores']}"
        )

        if resumen.get("participacion_porcentaje"):
            logger.info(
                f"📈 Participación: "
                f"{resumen['participacion_porcentaje']:.1f}%"
            )

        if resumen.get("cobertura_porcentaje"):
            logger.info(
                f"🎯 Cobertura: {resumen['cobertura_porcentaje']:.1f}%"
            )

        logger.info(
            f"📉 Guardias/profesor: {resumen['promedio_guardias']:.1f} "
            f"(min: {resumen['min_guardias']}, max: {resumen['max_guardias']})"
        )

        if resumen.get("desviacion_promedio"):
            logger.info(
                f"⚖️  Desviación promedio: "
                f"{resumen['desviacion_promedio']*100:.1f}%"
            )

        logger.info(
            f"⚠️  Balance: {resumen['balance']:.3f} "
            f"({'equilibrado' if resumen['balance'] < 0.2 else 'desequilibrado'})"
        )

        if resumen["profesores_sin_guardias"] > 0:
            logger.warning(
                f"⚠️  {resumen['profesores_sin_guardias']} "
                f"profesores sin guardias"
            )

        if resumen["conflictos_mismo_dia"] > 0:
            logger.error(
                f"❌ {resumen['conflictos_mismo_dia']} "
                f"conflictos (profesor con 2+ guardias mismo día)"
            )

        logger.info("═" * 60)
