"""
Dashboard de Observabilidad

Widget para visualizar métricas, health checks y performance en tiempo real.
"""

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.observability import (
    HealthChecker,
    get_metrics,
    get_performance_monitor,
)
from database.db_manager import SessionLocal


class ObservabilityDashboard(QDialog):
    """
    Dashboard principal de observabilidad.

    Muestra en tiempo real:
    - Health checks del sistema
    - Métricas de operaciones
    - Performance y operaciones lentas
    """

    # Señal para actualizar datos
    data_updated = pyqtSignal()

    def __init__(self, parent=None):
        """Inicializa el dashboard."""
        super().__init__(parent)
        self.setWindowTitle("📊 Observabilidad del Sistema")
        self.resize(900, 700)

        self.metrics = get_metrics()
        self.performance_monitor = get_performance_monitor()

        self._setup_ui()
        self._setup_timer()
        self._update_all()

    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_health_tab(), "🏥 Health Checks")
        tabs.addTab(self._create_metrics_tab(), "📊 Métricas")
        tabs.addTab(self._create_performance_tab(), "⚡ Performance")
        layout.addWidget(tabs)

        # Footer con botones
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Crea el encabezado del dashboard."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Título
        title = QLabel("📊 Observabilidad del Sistema")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Indicador de actualización
        self.status_label = QLabel("✅ Actualizado")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)

        return widget

    def _create_health_tab(self) -> QWidget:
        """Crea la pestaña de health checks."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Estado general
        self.health_status_group = QGroupBox("Estado General")
        health_status_layout = QVBoxLayout()
        self.health_overall_label = QLabel("Cargando...")
        self.health_overall_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        health_status_layout.addWidget(self.health_overall_label)
        self.health_status_group.setLayout(health_status_layout)
        layout.addWidget(self.health_status_group)

        # Componentes
        self.components_group = QGroupBox("Componentes del Sistema")
        self.components_layout = QVBoxLayout()
        self.components_group.setLayout(self.components_layout)

        # Scroll para componentes
        scroll = QScrollArea()
        scroll.setWidget(self.components_group)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Detalles en texto
        details_group = QGroupBox("Detalles Completos")
        details_layout = QVBoxLayout()
        self.health_details_text = QTextEdit()
        self.health_details_text.setReadOnly(True)
        self.health_details_text.setMaximumHeight(150)
        details_layout.addWidget(self.health_details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        return widget

    def _create_metrics_tab(self) -> QWidget:
        """Crea la pestaña de métricas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Resumen
        summary_group = QGroupBox("Resumen de Métricas")
        summary_layout = QVBoxLayout()
        self.metrics_summary_label = QLabel("Cargando...")
        summary_layout.addWidget(self.metrics_summary_label)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Métricas Prometheus
        prom_group = QGroupBox("Métricas Prometheus")
        prom_layout = QVBoxLayout()
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        prom_layout.addWidget(self.metrics_text)
        prom_group.setLayout(prom_layout)
        layout.addWidget(prom_group)

        return widget

    def _create_performance_tab(self) -> QWidget:
        """Crea la pestaña de performance."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Resumen
        summary_group = QGroupBox("Resumen de Performance")
        summary_layout = QVBoxLayout()
        self.perf_summary_label = QLabel("Cargando...")
        summary_layout.addWidget(self.perf_summary_label)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Alertas
        alerts_group = QGroupBox("⚠️ Alertas Activas")
        alerts_layout = QVBoxLayout()
        self.alerts_label = QLabel("Sin alertas")
        self.alerts_label.setWordWrap(True)
        alerts_layout.addWidget(self.alerts_label)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # Operaciones lentas
        slow_group = QGroupBox("🐌 Operaciones Más Lentas (Top 10)")
        slow_layout = QVBoxLayout()
        self.slow_ops_text = QTextEdit()
        self.slow_ops_text.setReadOnly(True)
        self.slow_ops_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        self.slow_ops_text.setMaximumHeight(200)
        slow_layout.addWidget(self.slow_ops_text)
        slow_group.setLayout(slow_layout)
        layout.addWidget(slow_group)

        # Estadísticas por operación
        stats_group = QGroupBox("📊 Estadísticas por Operación")
        stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        return widget

    def _create_footer(self) -> QWidget:
        """Crea el pie del dashboard."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Auto-refresh toggle
        self.auto_refresh_btn = QPushButton("⏸️ Pausar Auto-actualización")
        self.auto_refresh_btn.clicked.connect(self._toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_btn)

        # Refresh manual
        refresh_btn = QPushButton("🔄 Actualizar Ahora")
        refresh_btn.clicked.connect(self._update_all)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        # Cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return widget

    def _setup_timer(self):
        """Configura el timer para auto-actualización."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_all)
        self.timer.start(5000)  # Actualizar cada 5 segundos
        self.auto_refresh_enabled = True

    def _toggle_auto_refresh(self):
        """Activa/desactiva la auto-actualización."""
        self.auto_refresh_enabled = not self.auto_refresh_enabled

        if self.auto_refresh_enabled:
            self.timer.start(5000)
            self.auto_refresh_btn.setText("⏸️ Pausar Auto-actualización")
        else:
            self.timer.stop()
            self.auto_refresh_btn.setText("▶️ Reanudar Auto-actualización")

    def _update_all(self):
        """Actualiza todos los datos del dashboard."""
        self.status_label.setText("🔄 Actualizando...")
        self.status_label.setStyleSheet("color: orange;")

        try:
            self._update_health_checks()
            self._update_metrics()
            self._update_performance()

            self.status_label.setText("✅ Actualizado")
            self.status_label.setStyleSheet("color: green;")
            self.data_updated.emit()

        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: red;")

    def _update_health_checks(self):
        """Actualiza los health checks."""
        session = SessionLocal()

        try:
            checker = HealthChecker(session)
            health_status = checker.check_all()
            health_data = health_status.to_dict()

            # Estado general
            status = health_data["status"]
            status_emoji = {
                "HEALTHY": "✅",
                "DEGRADED": "⚠️",
                "UNHEALTHY": "❌",
            }.get(status, "❓")

            self.health_overall_label.setText(f"{status_emoji} {status}")

            # Limpiar componentes anteriores
            while self.components_layout.count():
                item = self.components_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Agregar componentes
            for component_data in health_data["components"]:
                component_name = component_data["name"]
                comp_widget = self._create_component_widget(
                    component_name, component_data
                )
                self.components_layout.addWidget(comp_widget)

            # Detalles en texto
            import json
            details_text = json.dumps(health_data, indent=2, ensure_ascii=False)
            self.health_details_text.setPlainText(details_text)

        finally:
            session.close()

    def _create_component_widget(
        self, component_name: str, component_data: dict
    ) -> QWidget:
        """Crea un widget para un componente de health check."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Status emoji
        status = component_data["status"]
        emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓",
        }.get(status, "❓")

        status_label = QLabel(emoji)
        status_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(status_label)

        # Nombre
        name_label = QLabel(component_name.replace("_", " ").title())
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)

        # Response time
        response_time = component_data.get("response_time_ms", "N/A")
        if response_time != "N/A":
            time_label = QLabel(f"{response_time:.2f}ms")
            time_label.setStyleSheet("color: gray;")
            layout.addWidget(time_label)

        layout.addStretch()

        # Detalles en tooltip
        details = component_data.get("details", {})
        if details:
            details_str = "\n".join(f"{k}: {v}" for k, v in details.items())
            widget.setToolTip(details_str)

        return widget

    def _update_metrics(self):
        """Actualiza las métricas."""
        summary = self.metrics.get_summary()

        # Resumen
        summary_text = f"""
Estado: {'✅ Prometheus Activo' if summary['prometheus_available'] else '⚠️ Modo Memoria'}
Métricas Registradas: {summary['metrics_count']}
Registros en Memoria: {summary['memory_store_size']}
        """.strip()
        self.metrics_summary_label.setText(summary_text)

        # Métricas Prometheus
        metrics_text = self.metrics.get_metrics_text()
        self.metrics_text.setPlainText(metrics_text)

    def _update_performance(self):
        """Actualiza las estadísticas de performance."""
        summary = self.performance_monitor.get_summary()

        # Resumen
        summary_text = f"""
Total Operaciones: {summary['total_operations']}
Operaciones Lentas: {summary['slow_operations']} ({summary['slow_percentage']:.2f}%)
Operaciones Recientes (5min): {summary['recent_operations_5min']}
Tipos de Operaciones: {summary['tracked_operation_types']}
Alertas Activas: {summary['active_alerts']}
Umbral Lento: {summary['slow_threshold_ms']}ms
        """.strip()
        self.perf_summary_label.setText(summary_text)

        # Alertas
        alerts = self.performance_monitor.get_alerts(clear=False)
        if alerts:
            alerts_text = "\n\n".join(f"• {alert}" for alert in alerts)
            self.alerts_label.setText(alerts_text)
            self.alerts_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.alerts_label.setText("✅ Sin alertas activas")
            self.alerts_label.setStyleSheet("color: green;")

        # Operaciones lentas
        slow_ops = self.performance_monitor.get_slow_operations(limit=10)
        if slow_ops:
            slow_text = f"{'#':<3} {'Operación':<30} {'Duración':<12} {'Timestamp'}\n"
            slow_text += "-" * 80 + "\n"
            for i, op in enumerate(slow_ops, 1):
                timestamp = op.timestamp.strftime("%H:%M:%S")
                slow_text += (
                    f"{i:<3} {op.operation:<30} {op.duration_ms:>8.2f}ms  {timestamp}\n"
                )
            self.slow_ops_text.setPlainText(slow_text)
        else:
            self.slow_ops_text.setPlainText("✅ No hay operaciones lentas registradas")

        # Estadísticas por operación
        all_stats = self.performance_monitor.get_all_operations_stats()
        if all_stats:
            stats_text = f"{'Operación':<30} {'Count':<8} {'Avg':<10} {'P95':<10} {'Slow'}\n"
            stats_text += "-" * 80 + "\n"
            for stats in all_stats[:10]:
                stats_text += (
                    f"{stats.operation:<30} {stats.count:<8} "
                    f"{stats.avg_duration_ms:>7.2f}ms {stats.p95_duration_ms:>7.2f}ms "
                    f"{stats.slow_operations}\n"
                )
            self.stats_text.setPlainText(stats_text)
        else:
            self.stats_text.setPlainText("⚠️ No hay estadísticas disponibles todavía")

    def closeEvent(self, event):
        """Maneja el cierre del dashboard."""
        if self.timer.isActive():
            self.timer.stop()
        event.accept()
