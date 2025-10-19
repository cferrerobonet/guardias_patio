"""
Dashboard de Observabilidad - Monitorización del sistema en tiempo real.

Proporciona visualización de:
- Métricas de caché (hit rate, tamaño, evictions)
- Gráficos de rendimiento
- Tracking de queries lentas
- Información del sistema
"""

from datetime import datetime
from typing import Dict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.cache import (
    get_cache_entries_info,
    get_cache_stats,
    get_function_metrics,
    invalidate_cache,
    reset_cache_stats,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class DashboardObservabilidad(QWidget):
    """
    Widget principal del dashboard de observabilidad.
    
    Muestra métricas del sistema en tiempo real con actualización automática.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.init_ui()
        self.init_auto_refresh()
        self.logger.info("Dashboard de Observabilidad inicializado")

    def init_ui(self):
        """Inicializa la interfaz del dashboard."""
        layout = QVBoxLayout(self)

        # Header con título y controles
        header = self._crear_header()
        layout.addWidget(header)

        # Tabs para diferentes vistas
        tabs = QTabWidget()
        tabs.addTab(self._crear_tab_metricas_cache(), "📊 Métricas Caché")
        tabs.addTab(self._crear_tab_funciones(), "📈 Por Función")
        tabs.addTab(self._crear_tab_entradas_cache(), "🗄️ Entradas Caché")
        tabs.addTab(self._crear_tab_sistema(), "💻 Sistema")

        layout.addWidget(tabs)

        self.setLayout(layout)

    def _crear_header(self) -> QWidget:
        """Crea el header con título y controles."""
        header = QWidget()
        layout = QHBoxLayout(header)

        # Título
        titulo = QLabel("🔍 Dashboard de Observabilidad")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(titulo)

        layout.addStretch()

        # Indicador de última actualización
        self.label_ultima_actualizacion = QLabel("Última actualización: --:--:--")
        self.label_ultima_actualizacion.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(self.label_ultima_actualizacion)

        # Botón refrescar manual
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.actualizar_metricas)
        btn_refresh.setToolTip("Actualizar métricas manualmente")
        layout.addWidget(btn_refresh)

        # Botón limpiar caché
        btn_clear = QPushButton("🗑️ Limpiar Caché")
        btn_clear.clicked.connect(self.limpiar_cache)
        btn_clear.setToolTip("Invalidar todas las entradas del caché")
        layout.addWidget(btn_clear)

        # Botón resetear estadísticas
        btn_reset = QPushButton("📊 Reset Stats")
        btn_reset.clicked.connect(self.resetear_estadisticas)
        btn_reset.setToolTip("Reiniciar contadores de estadísticas")
        layout.addWidget(btn_reset)

        return header

    def _crear_tab_metricas_cache(self) -> QWidget:
        """Crea la pestaña de métricas generales del caché."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Métricas principales en tarjetas
        cards_layout = QHBoxLayout()

        self.label_hit_rate = self._crear_card_metrica(
            "Hit Rate", "0.0%", "#27ae60", "Porcentaje de aciertos en caché"
        )
        cards_layout.addWidget(self.label_hit_rate)

        self.label_total_requests = self._crear_card_metrica(
            "Total Requests", "0", "#3498db", "Número total de consultas"
        )
        cards_layout.addWidget(self.label_total_requests)

        self.label_cache_size = self._crear_card_metrica(
            "Tamaño Caché", "0 / 1000", "#e67e22", "Entradas en caché / máximo"
        )
        cards_layout.addWidget(self.label_cache_size)

        self.label_evictions = self._crear_card_metrica(
            "Evictions", "0", "#e74c3c", "Entradas eliminadas por límite"
        )
        cards_layout.addWidget(self.label_evictions)

        layout.addLayout(cards_layout)

        # Detalles en texto
        group_detalles = QGroupBox("📋 Detalles de Estadísticas")
        detalles_layout = QVBoxLayout()

        self.text_detalles_cache = QTextEdit()
        self.text_detalles_cache.setReadOnly(True)
        self.text_detalles_cache.setMaximumHeight(200)
        self.text_detalles_cache.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        detalles_layout.addWidget(self.text_detalles_cache)

        group_detalles.setLayout(detalles_layout)
        layout.addWidget(group_detalles)

        # Gráfico de distribución (simulado con barras de texto)
        group_grafico = QGroupBox("📊 Distribución Hits vs Misses")
        grafico_layout = QVBoxLayout()

        self.label_hits_bar = QLabel()
        self.label_misses_bar = QLabel()
        grafico_layout.addWidget(QLabel("Hits:"))
        grafico_layout.addWidget(self.label_hits_bar)
        grafico_layout.addWidget(QLabel("Misses:"))
        grafico_layout.addWidget(self.label_misses_bar)

        group_grafico.setLayout(grafico_layout)
        layout.addWidget(group_grafico)

        layout.addStretch()
        return widget

    def _crear_tab_funciones(self) -> QWidget:
        """Crea la pestaña de métricas por función."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Información
        info = QLabel("📈 Rendimiento de caché por función (ordenado por total requests)")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)

        # Tabla de funciones
        self.tabla_funciones = QTableWidget()
        self.tabla_funciones.setColumnCount(5)
        self.tabla_funciones.setHorizontalHeaderLabels([
            "Función", "Hits", "Misses", "Total", "Hit Rate %"
        ])

        # Configurar tabla
        header = self.tabla_funciones.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_funciones.setAlternatingRowColors(True)
        self.tabla_funciones.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.tabla_funciones)

        return widget

    def _crear_tab_entradas_cache(self) -> QWidget:
        """Crea la pestaña de entradas individuales del caché."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Información
        info_layout = QHBoxLayout()
        info = QLabel("🗄️ Entradas en caché (ordenadas por accesos)")
        info.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(info)

        info_layout.addStretch()

        # Botón para mostrar solo activas
        self.check_solo_activas = QPushButton("🟢 Solo Activas")
        self.check_solo_activas.setCheckable(True)
        self.check_solo_activas.setChecked(True)
        self.check_solo_activas.clicked.connect(self.actualizar_metricas)
        info_layout.addWidget(self.check_solo_activas)

        layout.addLayout(info_layout)

        # Tabla de entradas
        self.tabla_entradas = QTableWidget()
        self.tabla_entradas.setColumnCount(6)
        self.tabla_entradas.setHorizontalHeaderLabels([
            "Key", "Accesos", "TTL (s)", "Edad (s)", "Expira en", "Estado"
        ])

        # Configurar tabla
        header = self.tabla_entradas.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_entradas.setAlternatingRowColors(True)
        self.tabla_entradas.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.tabla_entradas)

        return widget

    def _crear_tab_sistema(self) -> QWidget:
        """Crea la pestaña de información del sistema."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Información del sistema
        group_sistema = QGroupBox("💻 Información del Sistema")
        sistema_layout = QVBoxLayout()

        self.text_sistema = QTextEdit()
        self.text_sistema.setReadOnly(True)
        self.text_sistema.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)

        sistema_layout.addWidget(self.text_sistema)
        group_sistema.setLayout(sistema_layout)
        layout.addWidget(group_sistema)

        # Recomendaciones
        group_recomendaciones = QGroupBox("💡 Recomendaciones de Optimización")
        rec_layout = QVBoxLayout()

        self.text_recomendaciones = QTextEdit()
        self.text_recomendaciones.setReadOnly(True)
        self.text_recomendaciones.setStyleSheet("""
            QTextEdit {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)

        rec_layout.addWidget(self.text_recomendaciones)
        group_recomendaciones.setLayout(rec_layout)
        layout.addWidget(group_recomendaciones)

        layout.addStretch()
        return widget

    def _crear_card_metrica(
        self, titulo: str, valor: str, color: str, tooltip: str
    ) -> QGroupBox:
        """
        Crea una tarjeta para mostrar una métrica.
        
        Args:
            titulo: Título de la métrica
            valor: Valor inicial
            color: Color de acento
            tooltip: Descripción de la métrica
        
        Returns:
            QGroupBox configurado como tarjeta
        """
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        card.setToolTip(tooltip)

        layout = QVBoxLayout()

        # Título
        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_titulo)

        # Valor
        label_valor = QLabel(valor)
        label_valor.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        label_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_valor)

        card.setLayout(layout)

        # Guardar referencia al label de valor para actualizar
        card.label_valor = label_valor

        return card

    def init_auto_refresh(self):
        """Inicializa el timer para actualización automática."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_metricas)
        self.timer.start(5000)  # Actualizar cada 5 segundos

        # Primera actualización inmediata
        self.actualizar_metricas()

    def actualizar_metricas(self):
        """Actualiza todas las métricas del dashboard."""
        try:
            # Obtener estadísticas
            stats = get_cache_stats()

            # Actualizar cards de métricas principales
            self.label_hit_rate.label_valor.setText(f"{stats['hit_rate']:.1f}%")
            self.label_total_requests.label_valor.setText(
                str(stats['hits'] + stats['misses'])
            )
            self.label_cache_size.label_valor.setText(
                f"{stats['size']} / {stats['max_size']}"
            )
            self.label_evictions.label_valor.setText(str(stats['evictions']))

            # Actualizar detalles de caché
            self._actualizar_detalles_cache(stats)

            # Actualizar barras de distribución
            self._actualizar_barras_distribucion(stats)

            # Actualizar tabla de funciones
            self._actualizar_tabla_funciones()

            # Actualizar tabla de entradas
            self._actualizar_tabla_entradas()

            # Actualizar información del sistema
            self._actualizar_info_sistema(stats)

            # Actualizar recomendaciones
            self._actualizar_recomendaciones(stats)

            # Actualizar timestamp
            ahora = datetime.now().strftime("%H:%M:%S")
            self.label_ultima_actualizacion.setText(f"Última actualización: {ahora}")

            self.logger.debug("Métricas actualizadas correctamente")

        except Exception as e:
            self.logger.error(f"Error actualizando métricas: {e}")

    def _actualizar_detalles_cache(self, stats: Dict):
        """Actualiza el texto de detalles del caché."""
        texto = f"""
╔══════════════════════════════════════════════════════════════╗
║              ESTADÍSTICAS DETALLADAS DEL CACHÉ               ║
╚══════════════════════════════════════════════════════════════╝

📊 Métricas de Rendimiento:
   • Total Hits:        {stats['hits']:,}
   • Total Misses:      {stats['misses']:,}
   • Total Requests:    {stats['hits'] + stats['misses']:,}
   • Hit Rate:          {stats['hit_rate']:.2f}%
   
💾 Capacidad:
   • Entradas Actuales: {stats['size']:,}
   • Capacidad Máxima:  {stats['max_size']:,}
   • Uso:               {(stats['size'] / stats['max_size'] * 100):.1f}%
   
🗑️ Gestión de Memoria:
   • Evictions:         {stats['evictions']:,}
   • Invalidations:     {stats['invalidations']:,}
   
⏱️ Eficiencia:
   • Cache Miss Rate:   {100 - stats['hit_rate']:.2f}%
        """
        self.text_detalles_cache.setText(texto.strip())

    def _actualizar_barras_distribucion(self, stats: Dict):
        """Actualiza las barras visuales de distribución."""
        total = stats['hits'] + stats['misses']
        if total == 0:
            hits_pct = 0
            misses_pct = 0
        else:
            hits_pct = (stats['hits'] / total) * 100
            misses_pct = (stats['misses'] / total) * 100

        # Crear barra visual (50 caracteres max)
        hits_bar = "█" * int(hits_pct / 2)
        misses_bar = "█" * int(misses_pct / 2)

        self.label_hits_bar.setText(
            f"{hits_bar} {stats['hits']:,} ({hits_pct:.1f}%)"
        )
        self.label_hits_bar.setStyleSheet("color: #27ae60; font-family: monospace;")

        self.label_misses_bar.setText(
            f"{misses_bar} {stats['misses']:,} ({misses_pct:.1f}%)"
        )
        self.label_misses_bar.setStyleSheet("color: #e74c3c; font-family: monospace;")

    def _actualizar_tabla_funciones(self):
        """Actualiza la tabla de métricas por función."""
        try:
            metrics = get_function_metrics()

            # Ordenar por total requests (descendente)
            sorted_metrics = sorted(
                metrics.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            )

            self.tabla_funciones.setRowCount(len(sorted_metrics))

            for row, (func_name, data) in enumerate(sorted_metrics):
                # Función
                item_func = QTableWidgetItem(func_name)
                self.tabla_funciones.setItem(row, 0, item_func)

                # Hits
                item_hits = QTableWidgetItem(str(data['hits']))
                item_hits.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_funciones.setItem(row, 1, item_hits)

                # Misses
                item_misses = QTableWidgetItem(str(data['misses']))
                item_misses.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_funciones.setItem(row, 2, item_misses)

                # Total
                item_total = QTableWidgetItem(str(data['total']))
                item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_funciones.setItem(row, 3, item_total)

                # Hit Rate
                item_rate = QTableWidgetItem(f"{data['hit_rate']:.1f}%")
                item_rate.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Colorear según hit rate
                if data['hit_rate'] >= 80:
                    item_rate.setBackground(Qt.GlobalColor.green)
                elif data['hit_rate'] >= 50:
                    item_rate.setBackground(Qt.GlobalColor.yellow)
                else:
                    item_rate.setBackground(Qt.GlobalColor.red)

                self.tabla_funciones.setItem(row, 4, item_rate)

        except Exception as e:
            self.logger.error(f"Error actualizando tabla de funciones: {e}")

    def _actualizar_tabla_entradas(self):
        """Actualiza la tabla de entradas del caché."""
        try:
            entradas = get_cache_entries_info()

            # Filtrar solo activas si está marcado
            if self.check_solo_activas.isChecked():
                entradas = [e for e in entradas if not e['expired']]

            # Ordenar por accesos (descendente)
            entradas_sorted = sorted(
                entradas,
                key=lambda x: x['access_count'],
                reverse=True
            )

            # Limitar a 100 entradas para rendimiento
            entradas_sorted = entradas_sorted[:100]

            self.tabla_entradas.setRowCount(len(entradas_sorted))

            for row, entrada in enumerate(entradas_sorted):
                # Key (truncada)
                key = entrada['key']
                if len(key) > 60:
                    key = key[:57] + "..."
                item_key = QTableWidgetItem(key)
                item_key.setToolTip(entrada['key'])  # Full key en tooltip
                self.tabla_entradas.setItem(row, 0, item_key)

                # Accesos
                item_accesos = QTableWidgetItem(str(entrada['access_count']))
                item_accesos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_entradas.setItem(row, 1, item_accesos)

                # TTL
                item_ttl = QTableWidgetItem(f"{entrada['ttl']:.0f}")
                item_ttl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_entradas.setItem(row, 2, item_ttl)

                # Edad
                item_edad = QTableWidgetItem(f"{entrada['age']:.1f}")
                item_edad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_entradas.setItem(row, 3, item_edad)

                # Tiempo restante
                tiempo_restante = entrada['remaining_time']
                if tiempo_restante > 0:
                    item_restante = QTableWidgetItem(f"{tiempo_restante:.1f}s")
                else:
                    item_restante = QTableWidgetItem("EXPIRADA")
                    item_restante.setBackground(Qt.GlobalColor.red)
                item_restante.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_entradas.setItem(row, 4, item_restante)

                # Estado
                if entrada['expired']:
                    estado = "🔴 Expirada"
                    color = Qt.GlobalColor.red
                elif tiempo_restante < 60:
                    estado = "🟡 Por expirar"
                    color = Qt.GlobalColor.yellow
                else:
                    estado = "🟢 Activa"
                    color = Qt.GlobalColor.green

                item_estado = QTableWidgetItem(estado)
                item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_estado.setBackground(color)
                self.tabla_entradas.setItem(row, 5, item_estado)

        except Exception as e:
            self.logger.error(f"Error actualizando tabla de entradas: {e}")

    def _actualizar_info_sistema(self, stats: Dict):
        """Actualiza la información del sistema."""
        import platform
        import sys

        texto = f"""
╔══════════════════════════════════════════════════════════════╗
║                  INFORMACIÓN DEL SISTEMA                     ║
╚══════════════════════════════════════════════════════════════╝

🖥️ Sistema Operativo:
   • Plataforma:  {platform.system()} {platform.release()}
   • Arquitectura: {platform.machine()}
   
🐍 Python:
   • Versión:     {sys.version.split()[0]}
   • Implementación: {platform.python_implementation()}
   
💾 Caché:
   • Tipo:        OrderedDict (LRU)
   • Capacidad:   {stats['max_size']:,} entradas
   • Ocupación:   {stats['size']:,} entradas ({(stats['size'] / stats['max_size'] * 100):.1f}%)
   • TTL Default: 300 segundos
   
📊 Rendimiento:
   • Hit Rate:    {stats['hit_rate']:.2f}%
   • Evictions:   {stats['evictions']:,}
   • Eficiencia:  {'🟢 Excelente' if stats['hit_rate'] >= 80 else '🟡 Buena' if stats['hit_rate'] >= 50 else '🔴 Mejorable'}
        """
        self.text_sistema.setText(texto.strip())

    def _actualizar_recomendaciones(self, stats: Dict):
        """Actualiza las recomendaciones de optimización."""
        recomendaciones = []

        # Analizar hit rate
        if stats['hit_rate'] < 50:
            recomendaciones.append(
                "⚠️ Hit Rate bajo (< 50%): Considera aumentar el TTL de las entradas "
                "más consultadas o revisar patrones de acceso."
            )
        elif stats['hit_rate'] >= 90:
            recomendaciones.append(
                "✅ Excelente Hit Rate (>= 90%): El caché está funcionando óptimamente."
            )

        # Analizar uso de capacidad
        uso_pct = (stats['size'] / stats['max_size']) * 100
        if uso_pct > 90:
            recomendaciones.append(
                f"⚠️ Caché casi lleno ({uso_pct:.1f}%): Considera aumentar MAX_CACHE_SIZE "
                "o implementar invalidación más agresiva."
            )
        elif uso_pct < 30:
            recomendaciones.append(
                f"💡 Caché con baja ocupación ({uso_pct:.1f}%): El límite actual es suficiente."
            )

        # Analizar evictions
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            eviction_rate = (stats['evictions'] / total_requests) * 100
            if eviction_rate > 10:
                recomendaciones.append(
                    f"⚠️ Alta tasa de evictions ({eviction_rate:.1f}%): Considera aumentar "
                    "MAX_CACHE_SIZE para reducir eliminaciones forzadas."
                )

        # Si no hay recomendaciones, todo está bien
        if not recomendaciones:
            recomendaciones.append(
                "✅ Sistema funcionando correctamente. No hay recomendaciones en este momento."
            )

        texto = "\n\n".join(recomendaciones)
        self.text_recomendaciones.setText(texto)

    def limpiar_cache(self):
        """Limpia todas las entradas del caché."""
        try:
            # Invalidar todo el caché
            invalidate_cache("")  # Pattern vacío invalida todo

            self.logger.info("Caché limpiado manualmente")

            # Actualizar métricas inmediatamente
            self.actualizar_metricas()

        except Exception as e:
            self.logger.error(f"Error limpiando caché: {e}")

    def resetear_estadisticas(self):
        """Resetea los contadores de estadísticas."""
        try:
            reset_cache_stats()

            self.logger.info("Estadísticas reseteadas")

            # Actualizar métricas inmediatamente
            self.actualizar_metricas()

        except Exception as e:
            self.logger.error(f"Error reseteando estadísticas: {e}")

    def closeEvent(self, event):
        """Detiene el timer al cerrar el widget."""
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)
