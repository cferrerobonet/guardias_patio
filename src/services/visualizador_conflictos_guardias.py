"""
Sistema de visualización de conflictos y análisis gráfico de guardias.
Genera gráficos con matplotlib mostrando slots problemáticos, heatmaps y análisis.
"""
import logging
from datetime import date
from pathlib import Path
from typing import List, Optional

import matplotlib

matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from models.models import Configuracion, Guardia, Profesor
from services.validators import TurnoValidator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Instancia del validador de turnos
_turno_validator = TurnoValidator()


class VisualizadorConflictosGuardias:
    """
    Genera visualizaciones gráficas de la asignación de guardias
    para identificar problemas visualmente.
    """

    def __init__(self, db: Session, config: Configuracion, dias_lectivos: List[date]):
        self.db = db
        self.config = config
        self.dias_lectivos = dias_lectivos

        # Estilo
        plt.style.use('seaborn-v0_8-darkgrid')

    def generar_dashboard_completo(
        self,
        guardias: List[Guardia],
        ruta_salida: Optional[Path] = None
    ) -> Path:
        """
        Genera un dashboard completo con múltiples visualizaciones.

        Returns:
            Ruta del archivo PNG generado
        """
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle(
            'Dashboard de Análisis de Guardias',
            fontsize=20,
            fontweight='bold',
            y=0.98
        )

        # Crear grid de subplots
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # 1. Heatmap de cobertura por día
        ax1 = fig.add_subplot(gs[0, :2])
        self._generar_heatmap_cobertura_dia(guardias, ax1)

        # 2. Distribución por zona
        ax2 = fig.add_subplot(gs[0, 2])
        self._generar_distribucion_zonas(guardias, ax2)

        # 3. Timeline de cobertura
        ax3 = fig.add_subplot(gs[1, :])
        self._generar_timeline_cobertura(guardias, ax3)

        # 4. Carga por profesor (top 10)
        ax4 = fig.add_subplot(gs[2, 0])
        self._generar_carga_profesores(guardias, ax4)

        # 5. Distribución por turno
        ax5 = fig.add_subplot(gs[2, 1])
        self._generar_distribucion_turnos(guardias, ax5)

        # 6. Métricas resumen
        ax6 = fig.add_subplot(gs[2, 2])
        self._generar_metricas_resumen(guardias, ax6)

        # Guardar
        if ruta_salida is None:
            ruta_salida = Path("output/dashboard_guardias.png")

        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta_salida, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"✅ Dashboard generado: {ruta_salida}")
        return ruta_salida

    def _generar_heatmap_cobertura_dia(self, guardias: List[Guardia], ax):
        """Heatmap mostrando cobertura por día y recreo."""
        # Crear matriz de cobertura
        recreos = sorted(set(g.recreo for g in guardias))
        matriz_cobertura = np.zeros((len(recreos), len(self.dias_lectivos)))

        # Contar guardias por día-recreo
        for guardia in guardias:
            try:
                dia_idx = self.dias_lectivos.index(guardia.fecha)
                recreo_idx = recreos.index(guardia.recreo)
                matriz_cobertura[recreo_idx, dia_idx] += 1
            except ValueError:
                continue

        # Calcular cobertura esperada por recreo
        zonas_por_recreo = len(self.config.zonas)

        # Dibujar heatmap
        im = ax.imshow(
            matriz_cobertura,
            cmap='RdYlGn',
            aspect='auto',
            vmin=0,
            vmax=zonas_por_recreo
        )

        # Etiquetas
        ax.set_title('Cobertura por Día y Recreo', fontweight='bold')
        ax.set_ylabel('Recreo')
        ax.set_xlabel('Día Lectivo')

        # Ticks
        ax.set_yticks(range(len(recreos)))
        ax.set_yticklabels([f'R{r}' for r in recreos])

        # Mostrar cada N días en el eje X
        step = max(1, len(self.dias_lectivos) // 10)
        ax.set_xticks(range(0, len(self.dias_lectivos), step))
        ax.set_xticklabels(
            [self.dias_lectivos[i].strftime('%d/%m') for i in range(0, len(self.dias_lectivos), step)],
            rotation=45
        )

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Guardias Asignadas')

        # Marcar slots problemáticos
        for i in range(matriz_cobertura.shape[0]):
            for j in range(matriz_cobertura.shape[1]):
                if matriz_cobertura[i, j] < zonas_por_recreo:
                    ax.plot(j, i, 'rx', markersize=3)

    def _generar_distribucion_zonas(self, guardias: List[Guardia], ax):
        """Gráfico de barras con distribución por zona."""
        zonas_count = {}
        for guardia in guardias:
            zonas_count[guardia.zona] = zonas_count.get(guardia.zona, 0) + 1

        zonas = sorted(zonas_count.keys())
        counts = [zonas_count[z] for z in zonas]

        # Calcular esperado
        total_slots = len(self.dias_lectivos) * len(self.config.recreos)
        esperado_por_zona = total_slots

        colors = ['green' if c >= esperado_por_zona * 0.9 else 'orange' if c >= esperado_por_zona * 0.8 else 'red'
                  for c in counts]

        ax.bar(range(len(zonas)), counts, color=colors, alpha=0.7)
        ax.axhline(y=esperado_por_zona, color='blue', linestyle='--', label='Esperado')

        ax.set_title('Distribución por Zona', fontweight='bold')
        ax.set_xlabel('Zona')
        ax.set_ylabel('Número de Guardias')
        ax.set_xticks(range(len(zonas)))
        ax.set_xticklabels([f'Z{z}' for z in zonas])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

    def _generar_timeline_cobertura(self, guardias: List[Guardia], ax):
        """Timeline mostrando evolución de cobertura a lo largo del curso."""
        # Agrupar por día
        guardias_por_dia = {}
        for guardia in guardias:
            if guardia.fecha not in guardias_por_dia:
                guardias_por_dia[guardia.fecha] = 0
            guardias_por_dia[guardia.fecha] += 1

        # Crear arrays para el gráfico
        fechas = sorted(self.dias_lectivos)
        cobertura = [guardias_por_dia.get(f, 0) for f in fechas]

        # Cobertura esperada
        esperado = len(self.config.recreos) * len(self.config.zonas)

        # Graficar
        ax.plot(fechas, cobertura, label='Cobertura Real', linewidth=2, color='steelblue')
        ax.axhline(y=esperado, color='green', linestyle='--', label='Cobertura Esperada (100%)', linewidth=1.5)
        ax.axhline(y=esperado * 0.95, color='orange', linestyle=':', label='Mínimo Aceptable (95%)', linewidth=1)

        # Rellenar área debajo de la línea
        ax.fill_between(fechas, cobertura, alpha=0.3, color='steelblue')

        # Marcar días problemáticos
        dias_problematicos = [f for f in fechas if guardias_por_dia.get(f, 0) < esperado * 0.9]
        if dias_problematicos:
            cobertura_problematica = [guardias_por_dia.get(f, 0) for f in dias_problematicos]
            ax.scatter(dias_problematicos, cobertura_problematica, color='red', s=50, zorder=5, label='Días Críticos')

        ax.set_title('Timeline de Cobertura', fontweight='bold')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Guardias Asignadas por Día')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        # Formato de fechas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _generar_carga_profesores(self, guardias: List[Guardia], ax):
        """Top 10 profesores con más guardias."""
        profesores_count = {}
        for guardia in guardias:
            profesores_count[guardia.profesor_id] = profesores_count.get(guardia.profesor_id, 0) + 1

        # Top 10
        top_profesores = sorted(profesores_count.items(), key=lambda x: x[1], reverse=True)[:10]

        # Obtener nombres
        nombres = []
        counts = []
        for prof_id, count in top_profesores:
            profesor = self.db.query(Profesor).get(prof_id)
            nombre = profesor.nombre[:15] if profesor else f"ID {prof_id}"
            nombres.append(nombre)
            counts.append(count)

        # Graficar
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(nombres)))
        ax.barh(range(len(nombres)), counts, color=colors)

        ax.set_title('Top 10 Profesores (Más Guardias)', fontweight='bold')
        ax.set_xlabel('Número de Guardias')
        ax.set_yticks(range(len(nombres)))
        ax.set_yticklabels(nombres)
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=0.3)

    def _generar_distribucion_turnos(self, guardias: List[Guardia], ax):
        """Gráfico circular con distribución por turno."""
        turnos_count = {}
        for guardia in guardias:
            turnos_count[guardia.turno] = turnos_count.get(guardia.turno, 0) + 1

        turnos = list(turnos_count.keys())
        counts = list(turnos_count.values())

        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'][:len(turnos)]

        ax.pie(
            counts,
            labels=turnos,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10}
        )
        ax.set_title('Distribución por Turno', fontweight='bold')

    def _generar_metricas_resumen(self, guardias: List[Guardia], ax):
        """Panel con métricas resumidas."""
        ax.axis('off')

        # Calcular métricas
        total_slots = len(self.dias_lectivos) * len(self.config.recreos) * len(self.config.zonas)
        cobertura = (len(guardias) / total_slots * 100) if total_slots > 0 else 0

        profesores_con_guardias = len(set(g.profesor_id for g in guardias))
        profesores_activos = self.db.query(Profesor).filter(Profesor.activo.is_(True)).count()

        guardias_por_dia = len(guardias) / len(self.dias_lectivos) if self.dias_lectivos else 0

        # Texto con métricas
        texto = f"""
📊 MÉTRICAS GENERALES

✓ Guardias Asignadas
  {len(guardias):,} de {total_slots:,}

✓ Cobertura
  {cobertura:.1f}%

✓ Participación
  {profesores_con_guardias}/{profesores_activos} profesores

✓ Promedio Diario
  {guardias_por_dia:.1f} guardias/día

✓ Días Lectivos
  {len(self.dias_lectivos)} días
"""

        # Color según cobertura
        if cobertura >= 95:
            color_fondo = '#d4edda'
            color_texto = '#155724'
        elif cobertura >= 85:
            color_fondo = '#fff3cd'
            color_texto = '#856404'
        else:
            color_fondo = '#f8d7da'
            color_texto = '#721c24'

        ax.text(
            0.5, 0.5, texto,
            fontsize=11,
            verticalalignment='center',
            horizontalalignment='center',
            bbox=dict(boxstyle='round', facecolor=color_fondo, alpha=0.8),
            color=color_texto,
            fontfamily='monospace'
        )

        ax.set_title('Resumen', fontweight='bold', pad=20)

    def generar_analisis_slots_problematicos(
        self,
        guardias: List[Guardia],
        ruta_salida: Optional[Path] = None
    ) -> Path:
        """
        Genera visualización específica de slots problemáticos.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Análisis de Slots Problemáticos', fontsize=16, fontweight='bold')

        # 1. Slots vacíos por turno y zona
        self._generar_slots_vacios_turno_zona(guardias, ax1)

        # 2. Días con cobertura crítica
        self._generar_dias_criticos(guardias, ax2)

        # Guardar
        if ruta_salida is None:
            ruta_salida = Path("output/analisis_slots_problematicos.png")

        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta_salida, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"✅ Análisis de slots generado: {ruta_salida}")
        return ruta_salida

    def _generar_slots_vacios_turno_zona(self, guardias: List[Guardia], ax):
        """Heatmap de slots vacíos por turno y zona."""
        turnos = sorted(set(r.turno for r in self.config.recreos))
        zonas = sorted([z.id for z in self.config.zonas])

        # Calcular slots esperados y reales
        matriz_vacios = np.zeros((len(turnos), len(zonas)))

        for i, turno in enumerate(turnos):
            recreos_turno = [r for r in self.config.recreos if r.turno == turno]
            for j, zona in enumerate(zonas):
                esperado = len(self.dias_lectivos) * len(recreos_turno)
                real = len([g for g in guardias if g.turno == turno and g.zona == zona])
                matriz_vacios[i, j] = esperado - real

        # Heatmap
        im = ax.imshow(matriz_vacios, cmap='Reds', aspect='auto')

        ax.set_title('Slots Vacíos por Turno y Zona', fontweight='bold')
        ax.set_ylabel('Turno')
        ax.set_xlabel('Zona')
        ax.set_yticks(range(len(turnos)))
        ax.set_yticklabels(turnos)
        ax.set_xticks(range(len(zonas)))
        ax.set_xticklabels([f'Z{z}' for z in zonas])

        # Añadir valores en las celdas
        for i in range(len(turnos)):
            for j in range(len(zonas)):
                texto = ax.text(j, i, int(matriz_vacios[i, j]),
                               ha="center", va="center", color="black", fontweight='bold')

        plt.colorbar(im, ax=ax, label='Slots Vacíos')

    def _generar_dias_criticos(self, guardias: List[Guardia], ax):
        """Identifica y muestra días con cobertura crítica."""
        esperado_por_dia = len(self.config.recreos) * len(self.config.zonas)

        dias_cobertura = []
        for dia in self.dias_lectivos:
            guardias_dia = len([g for g in guardias if g.fecha == dia])
            porcentaje = (guardias_dia / esperado_por_dia * 100) if esperado_por_dia > 0 else 0
            dias_cobertura.append((dia, guardias_dia, porcentaje))

        # Filtrar días críticos (<90%)
        dias_criticos = [(d, c, p) for d, c, p in dias_cobertura if p < 90]

        if dias_criticos:
            fechas, counts, porcentajes = zip(*dias_criticos)

            colors = ['red' if p < 70 else 'orange' for p in porcentajes]

            ax.bar(range(len(fechas)), counts, color=colors, alpha=0.7)
            ax.axhline(y=esperado_por_dia, color='green', linestyle='--', label='Esperado (100%)')
            ax.axhline(y=esperado_por_dia * 0.9, color='orange', linestyle=':', label='Crítico (<90%)')

            ax.set_title(f'Días Críticos ({len(dias_criticos)} días con cobertura <90%)', fontweight='bold')
            ax.set_xlabel('Día')
            ax.set_ylabel('Guardias Asignadas')
            ax.set_xticks(range(len(fechas)))
            ax.set_xticklabels([f.strftime('%d/%m') for f in fechas], rotation=45)
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
        else:
            ax.text(0.5, 0.5, '✅ No hay días críticos\n(todos >90% cobertura)',
                   ha='center', va='center', fontsize=14, color='green')
            ax.axis('off')
