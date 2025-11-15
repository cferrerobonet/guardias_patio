"""
Sistema de Machine Learning Predictivo para optimizar asignación de guardias.
Aprende de soluciones pasadas y predice mejor estrategia inicial.
"""
import json
import logging
import pickle
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from models.models import Configuracion, Guardia, Profesor
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class HistoricoSolucion:
    """Registro histórico de una solución."""
    fecha: datetime
    caracteristicas_config: Dict
    estrategia_usada: str  # 'iterativo' o 'ilp'
    iteraciones_necesarias: int
    tiempo_segundos: float
    cobertura_final: float
    exito: bool
    parametros_usados: Dict


class MLPredictorEstrategia:
    """
    Predictor ML que aprende de soluciones pasadas para optimizar
    estrategia inicial y parámetros del algoritmo.
    """

    def __init__(self, db: Session, modelo_dir: Optional[Path] = None):
        self.db = db
        self.modelo_dir = modelo_dir or Path("data/ml_models")
        self.modelo_dir.mkdir(parents=True, exist_ok=True)

        # Modelos ML
        self.modelo_estrategia = None  # Predice estrategia óptima
        self.modelo_iteraciones = None  # Predice número de iteraciones necesarias
        self.scaler = None

        # Archivo de histórico
        self.archivo_historico = self.modelo_dir / "historico_soluciones.json"

        # Cargar modelos si existen
        self._cargar_modelos()

    def registrar_solucion(
        self,
        config: Configuracion,
        dias_lectivos: List[date],
        guardias: List[Guardia],
        estrategia_usada: str,
        iteraciones_necesarias: int,
        tiempo_segundos: float,
        parametros_usados: Dict
    ):
        """
        Registra una solución en el histórico para entrenamiento futuro.
        """
        # Calcular características
        caracteristicas = self._extraer_caracteristicas_config(config, dias_lectivos)

        # Calcular métricas
        total_slots = len(dias_lectivos) * len(config.recreos) * len(config.zonas)
        cobertura = (len(guardias) / total_slots) if total_slots > 0 else 0

        # Crear registro
        registro = HistoricoSolucion(
            fecha=datetime.now(),
            caracteristicas_config=caracteristicas,
            estrategia_usada=estrategia_usada,
            iteraciones_necesarias=iteraciones_necesarias,
            tiempo_segundos=tiempo_segundos,
            cobertura_final=cobertura,
            exito=cobertura >= 0.95,
            parametros_usados=parametros_usados
        )

        # Guardar en archivo
        self._append_historico(registro)

        logger.info(
            f"📚 Solución registrada para ML: {estrategia_usada}, "
            f"cobertura {cobertura*100:.1f}%"
        )

    def predecir_estrategia_optima(
        self,
        config: Configuracion,
        dias_lectivos: List[date]
    ) -> Tuple[str, Dict]:
        """
        Predice la mejor estrategia y parámetros iniciales basándose en ML.

        Returns:
            Tupla de (estrategia_recomendada, parametros_recomendados)
        """
        # Extraer características
        caracteristicas = self._extraer_caracteristicas_config(config, dias_lectivos)

        if self.modelo_estrategia is None or not self._tiene_datos_suficientes():
            # Sin modelo entrenado, usar heurística simple
            return self._predecir_heuristico(caracteristicas)

        # Preparar features para predicción
        X = self._preparar_features([caracteristicas])

        # Predecir estrategia
        estrategia_pred = self.modelo_estrategia.predict(X)[0]

        # Predecir iteraciones necesarias
        iteraciones_pred = int(self.modelo_iteraciones.predict(X)[0]) if self.modelo_iteraciones else 3

        # Determinar parámetros basados en predicción
        if estrategia_pred == 'iterativo':
            parametros = {
                'max_iteraciones': min(5, iteraciones_pred + 1),
                'objetivo_cobertura': 0.95,
                'usar_cache': True
            }
        else:  # ilp
            parametros = {
                'limite_tiempo': 300,
                'priorizar_fecha_inicio': True,
                'priorizar_equidad': True
            }

        logger.info(
            f"🤖 ML predice: {estrategia_pred} "
            f"(iteraciones estimadas: {iteraciones_pred})"
        )

        return estrategia_pred, parametros

    def entrenar_modelos(self):
        """
        Entrena los modelos ML con el histórico de soluciones.
        Requiere al menos 20 soluciones registradas.
        """
        # Cargar histórico
        historico = self._cargar_historico()

        if len(historico) < 20:
            logger.warning(
                f"⚠️  Insuficientes datos para entrenar ML "
                f"({len(historico)}/20 mínimo)"
            )
            return False

        logger.info(f"🤖 Entrenando modelos ML con {len(historico)} soluciones...")

        # Preparar datos
        X = []  # Features
        y_estrategia = []  # Target: estrategia usada
        y_iteraciones = []  # Target: iteraciones necesarias

        for solucion in historico:
            if solucion.exito:  # Solo aprender de soluciones exitosas
                features = self._dict_to_features(solucion.caracteristicas_config)
                X.append(features)
                y_estrategia.append(1 if solucion.estrategia_usada == 'ilp' else 0)
                y_iteraciones.append(solucion.iteraciones_necesarias)

        if len(X) < 10:
            logger.warning("⚠️  Muy pocas soluciones exitosas para entrenar")
            return False

        X = np.array(X)
        y_estrategia = np.array(y_estrategia)
        y_iteraciones = np.array(y_iteraciones)

        # Normalizar features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Entrenar modelo de estrategia (clasificación)
        self.modelo_estrategia = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.modelo_estrategia.fit(X_scaled, y_estrategia)

        # Entrenar modelo de iteraciones (regresión)
        from sklearn.ensemble import RandomForestRegressor
        self.modelo_iteraciones = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.modelo_iteraciones.fit(X_scaled, y_iteraciones)

        # Guardar modelos
        self._guardar_modelos()

        logger.info("✅ Modelos ML entrenados y guardados correctamente")
        return True

    def _extraer_caracteristicas_config(
        self,
        config: Configuracion,
        dias_lectivos: List[date]
    ) -> Dict:
        """Extrae características relevantes de la configuración."""
        profesores = self.db.query(Profesor).filter(
            Profesor.activo.is_(True)
        ).all()

        # Características numéricas básicas
        num_profesores = len(profesores)
        num_dias = len(dias_lectivos)
        num_recreos = len(config.recreos)
        num_zonas = len(config.zonas)

        # Características de complejidad
        total_slots = num_dias * num_recreos * num_zonas
        ratio_profesor_slots = num_profesores / total_slots if total_slots > 0 else 0

        # Ausencias promedio
        ausencias_promedio = np.mean([
            len(p.ausencias) if hasattr(p, 'ausencias') else 0
            for p in profesores
        ])

        # Distribución de turnos
        profesores_manana = sum(1 for p in profesores if 'mañana' in (p.turnos or []))
        profesores_tarde = sum(1 for p in profesores if 'tarde' in (p.turnos or []))

        # Distribución de zonas
        zonas_promedio_prof = np.mean([
            len(p.zonas) if p.zonas else 0
            for p in profesores
        ])

        return {
            'num_profesores': num_profesores,
            'num_dias': num_dias,
            'num_recreos': num_recreos,
            'num_zonas': num_zonas,
            'total_slots': total_slots,
            'ratio_profesor_slots': ratio_profesor_slots,
            'ausencias_promedio': ausencias_promedio,
            'profesores_manana': profesores_manana,
            'profesores_tarde': profesores_tarde,
            'zonas_promedio_prof': zonas_promedio_prof,
            'complejidad': total_slots / num_profesores if num_profesores > 0 else 0
        }

    def _dict_to_features(self, caracteristicas: Dict) -> List[float]:
        """Convierte diccionario de características a vector numpy."""
        return [
            caracteristicas.get('num_profesores', 0),
            caracteristicas.get('num_dias', 0),
            caracteristicas.get('num_recreos', 0),
            caracteristicas.get('num_zonas', 0),
            caracteristicas.get('total_slots', 0),
            caracteristicas.get('ratio_profesor_slots', 0),
            caracteristicas.get('ausencias_promedio', 0),
            caracteristicas.get('profesores_manana', 0),
            caracteristicas.get('profesores_tarde', 0),
            caracteristicas.get('zonas_promedio_prof', 0),
            caracteristicas.get('complejidad', 0)
        ]

    def _preparar_features(self, caracteristicas_list: List[Dict]) -> np.ndarray:
        """Prepara features para predicción."""
        X = np.array([self._dict_to_features(c) for c in caracteristicas_list])

        if self.scaler is not None:
            X = self.scaler.transform(X)

        return X

    def _predecir_heuristico(
        self,
        caracteristicas: Dict
    ) -> Tuple[str, Dict]:
        """Predicción heurística cuando no hay modelo entrenado."""
        complejidad = caracteristicas.get('complejidad', 0)
        ratio = caracteristicas.get('ratio_profesor_slots', 0)

        # Si la complejidad es alta o el ratio es bajo, recomendar ILP
        if complejidad > 40 or ratio < 0.05:
            estrategia = 'ilp'
            parametros = {
                'limite_tiempo': 300,
                'priorizar_fecha_inicio': True,
                'priorizar_equidad': True
            }
        else:
            estrategia = 'iterativo'
            parametros = {
                'max_iteraciones': 5,
                'objetivo_cobertura': 0.95,
                'usar_cache': True
            }

        logger.info(f"📊 Heurística predice: {estrategia} (complejidad: {complejidad:.1f})")
        return estrategia, parametros

    def _append_historico(self, registro: HistoricoSolucion):
        """Añade un registro al histórico."""
        historico = self._cargar_historico()
        historico.append(registro)

        # Guardar (mantener últimas 1000 soluciones)
        historico_reciente = historico[-1000:]

        with open(self.archivo_historico, 'w', encoding='utf-8') as f:
            json.dump(
                [asdict(r) for r in historico_reciente],
                f,
                indent=2,
                default=str
            )

    def _cargar_historico(self) -> List[HistoricoSolucion]:
        """Carga el histórico desde archivo."""
        if not self.archivo_historico.exists():
            return []

        try:
            with open(self.archivo_historico, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return [
                HistoricoSolucion(
                    fecha=datetime.fromisoformat(r['fecha']),
                    caracteristicas_config=r['caracteristicas_config'],
                    estrategia_usada=r['estrategia_usada'],
                    iteraciones_necesarias=r['iteraciones_necesarias'],
                    tiempo_segundos=r['tiempo_segundos'],
                    cobertura_final=r['cobertura_final'],
                    exito=r['exito'],
                    parametros_usados=r['parametros_usados']
                )
                for r in data
            ]
        except Exception as e:
            logger.error(f"Error al cargar histórico: {e}")
            return []

    def _tiene_datos_suficientes(self) -> bool:
        """Verifica si hay suficientes datos para predicción ML."""
        historico = self._cargar_historico()
        return len(historico) >= 20

    def _guardar_modelos(self):
        """Guarda los modelos entrenados en disco."""
        if self.modelo_estrategia:
            with open(self.modelo_dir / "modelo_estrategia.pkl", 'wb') as f:
                pickle.dump(self.modelo_estrategia, f)

        if self.modelo_iteraciones:
            with open(self.modelo_dir / "modelo_iteraciones.pkl", 'wb') as f:
                pickle.dump(self.modelo_iteraciones, f)

        if self.scaler:
            with open(self.modelo_dir / "scaler.pkl", 'wb') as f:
                pickle.dump(self.scaler, f)

    def _cargar_modelos(self):
        """Carga modelos desde disco si existen."""
        try:
            archivo_estrategia = self.modelo_dir / "modelo_estrategia.pkl"
            archivo_iteraciones = self.modelo_dir / "modelo_iteraciones.pkl"
            archivo_scaler = self.modelo_dir / "scaler.pkl"

            if archivo_estrategia.exists():
                with open(archivo_estrategia, 'rb') as f:
                    self.modelo_estrategia = pickle.load(f)
                logger.info("✅ Modelo de estrategia cargado")

            if archivo_iteraciones.exists():
                with open(archivo_iteraciones, 'rb') as f:
                    self.modelo_iteraciones = pickle.load(f)
                logger.info("✅ Modelo de iteraciones cargado")

            if archivo_scaler.exists():
                with open(archivo_scaler, 'rb') as f:
                    self.scaler = pickle.load(f)

        except Exception as e:
            logger.warning(f"⚠️  No se pudieron cargar modelos ML: {e}")

    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas del sistema ML."""
        historico = self._cargar_historico()

        if not historico:
            return {
                'total_soluciones': 0,
                'soluciones_exitosas': 0,
                'modelos_entrenados': False
            }

        exitosas = [s for s in historico if s.exito]

        estrategias_usadas = {}
        for s in exitosas:
            estrategias_usadas[s.estrategia_usada] = \
                estrategias_usadas.get(s.estrategia_usada, 0) + 1

        return {
            'total_soluciones': len(historico),
            'soluciones_exitosas': len(exitosas),
            'tasa_exito': len(exitosas) / len(historico) if historico else 0,
            'estrategias_usadas': estrategias_usadas,
            'tiempo_promedio': np.mean([s.tiempo_segundos for s in exitosas]) if exitosas else 0,
            'cobertura_promedio': np.mean([s.cobertura_final for s in exitosas]) if exitosas else 0,
            'modelos_entrenados': self.modelo_estrategia is not None,
            'datos_suficientes_entrenamiento': self._tiene_datos_suficientes()
        }
