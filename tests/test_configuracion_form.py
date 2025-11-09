"""
Tests para ConfiguracionForm.

Cobertura actual: 8.30%
Objetivo: >70%
"""

from datetime import date, time

import pytest
from presentation.forms.configuracion_form import ConfiguracionForm
from PyQt6.QtCore import QDate, QTime
from PyQt6.QtWidgets import QDateEdit, QPushButton, QTimeEdit

from models.models import Configuracion


@pytest.fixture
def config_completa(session):
    """Fixture que crea una configuración completa para tests."""
    config = Configuracion(
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(11, 30),
        hora_recreo1_tarde=time(17, 0),
        hora_recreo2_tarde=time(17, 30),
        activar_festivos_automaticos=True,
        dias_no_lectivos_personalizados="[]",
        recreos_config='[{"id": 1, "etiqueta": "Recreo 1", "turno": "manana"}]',
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0
    )
    session.add(config)
    session.commit()
    return config


@pytest.mark.ui
class TestConfiguracionFormBasico:
    """Tests básicos de ConfiguracionForm."""

    def test_crear_formulario(self, qtbot, session):
        """Test: Se puede crear un formulario de configuración."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert form.windowTitle() == "Configuración del Curso"

    def test_formulario_carga_config_existente(self, qtbot, session, config_completa):
        """Test: El formulario carga datos de configuración existente."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Verificar que se cargó la configuración
        assert form.fecha_inicio_input.date().toPyDate() == date(2024, 9, 1)
        assert form.fecha_fin_input.date().toPyDate() == date(2025, 6, 30)

    def test_formulario_sin_configuracion(self, qtbot, session):
        """Test: El formulario funciona sin configuración previa (valores por defecto)."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Debe existir el formulario y tener valores por defecto
        assert form is not None
        assert form.fecha_inicio_input is not None

    def test_botones_presentes(self, qtbot, session):
        """Test: Todos los botones necesarios están presentes."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        buttons = form.findChildren(QPushButton)
        assert len(buttons) > 0, "Debe haber al menos un botón en el formulario"


@pytest.mark.ui
class TestConfiguracionFormFechas:
    """Tests para manejo de fechas."""

    def test_campos_fecha_presentes(self, qtbot, session):
        """Test: Los campos de fecha están presentes."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form.fecha_inicio_input is not None
        assert form.fecha_fin_input is not None
        assert isinstance(form.fecha_inicio_input, QDateEdit)
        assert isinstance(form.fecha_fin_input, QDateEdit)

    def test_actualizar_fechas(self, qtbot, session, config_completa):
        """Test: Se pueden actualizar las fechas del curso."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Cambiar fechas
        nueva_fecha_inicio = QDate(2025, 9, 1)
        form.fecha_inicio_input.setDate(nueva_fecha_inicio)

        assert form.fecha_inicio_input.date() == nueva_fecha_inicio


@pytest.mark.ui
class TestConfiguracionFormRecreos:
    """Tests para configuración de recreos."""

    def test_campos_recreo_manana_presentes(self, qtbot, session):
        """Test: Los campos de recreo de mañana están presentes."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form.recreo1_manana_input is not None
        assert form.recreo2_manana_input is not None
        assert isinstance(form.recreo1_manana_input, QTimeEdit)
        assert isinstance(form.recreo2_manana_input, QTimeEdit)

    def test_campos_recreo_tarde_presentes(self, qtbot, session):
        """Test: Los campos de recreo de tarde están presentes."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form.recreo1_tarde_input is not None
        assert form.recreo2_tarde_input is not None
        assert isinstance(form.recreo1_tarde_input, QTimeEdit)
        assert isinstance(form.recreo2_tarde_input, QTimeEdit)

    def test_recreos_cargan_valores(self, qtbot, session, config_completa):
        """Test: Los recreos cargan valores desde la base de datos."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Verificar valores de mañana
        assert form.recreo1_manana_input.time().toPyTime() == time(11, 0)
        assert form.recreo2_manana_input.time().toPyTime() == time(11, 30)

        # Verificar valores de tarde
        assert form.recreo1_tarde_input.time().toPyTime() == time(17, 0)
        assert form.recreo2_tarde_input.time().toPyTime() == time(17, 30)


@pytest.mark.ui
class TestConfiguracionFormCamposAdicionales:
    """Tests para campos adicionales."""

    def test_campos_ajuste_presentes(self, qtbot, session):
        """Test: Los campos de ajuste están presentes."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form.ajuste_tutores_input is not None
        assert form.ajuste_no_tutores_input is not None

    def test_campos_festivos_presentes(self, qtbot, session):
        """Test: Los campos de festivos están presentes."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form.festivos_auto_input is not None
        assert form.no_lectivos_input is not None

    def test_campo_recreos_config_presente(self, qtbot, session):
        """Test: El campo de configuración de recreos está presente."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert form.recreos_config_input is not None


@pytest.mark.ui
class TestConfiguracionFormValidaciones:
    """Tests para validaciones del formulario."""

    def test_validar_formulario_existe(self, qtbot, session):
        """Test: El método validar_formulario existe."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, 'validar_formulario')
        assert callable(form.validar_formulario)

    def test_validar_formulario_retorna_tupla(self, qtbot, session, config_completa):
        """Test: validar_formulario retorna tupla (bool, str)."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        resultado = form.validar_formulario()
        assert isinstance(resultado, tuple)
        assert len(resultado) == 2
        assert isinstance(resultado[0], bool)
        assert isinstance(resultado[1], str)


@pytest.mark.ui
class TestConfiguracionFormGuardado:
    """Tests para operaciones de guardado."""

    def test_guardar_metodo_existe(self, qtbot, session):
        """Test: El método para guardar existe."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Buscar métodos relacionados con guardar/actualizar
        assert hasattr(form, 'actualizar_config_uc')

    def test_cargar_configuracion_metodo(self, qtbot, session, config_completa):
        """Test: El método cargar_configuracion funciona."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Llamar manualmente al método
        form.cargar_configuracion()

        # Verificar que cargó los datos
        assert form.fecha_inicio_input.date().toPyDate() == date(2024, 9, 1)


@pytest.mark.ui
class TestConfiguracionFormIntegracion:
    """Tests de integración."""

    def test_ciclo_completo_crear_config(self, qtbot, session):
        """Test: Ciclo completo de crear configuración."""
        # Sin configuración inicial
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Establecer valores
        form.fecha_inicio_input.setDate(QDate(2024, 9, 1))
        form.fecha_fin_input.setDate(QDate(2025, 6, 30))
        form.recreo1_manana_input.setTime(QTime(11, 0))
        form.recreo2_manana_input.setTime(QTime(11, 30))

        # Verificar valores
        assert form.fecha_inicio_input.date().toPyDate() == date(2024, 9, 1)
        assert form.fecha_fin_input.date().toPyDate() == date(2025, 6, 30)

    def test_actualizar_config_existente(self, qtbot, session, config_completa):
        """Test: Actualizar configuración existente."""
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        # Valores iniciales
        assert form.fecha_inicio_input.date().toPyDate() == date(2024, 9, 1)

        # Cambiar valor
        nueva_fecha = QDate(2025, 9, 1)
        form.fecha_inicio_input.setDate(nueva_fecha)

        # Verificar cambio
        assert form.fecha_inicio_input.date() == nueva_fecha


@pytest.mark.ui
@pytest.mark.slow
class TestConfiguracionFormRendimiento:
    """Tests de rendimiento."""

    def test_carga_rapida(self, qtbot, session, config_completa):
        """Test: El formulario debe cargar rápidamente."""
        import time as time_module

        start = time_module.time()
        form = ConfiguracionForm(session)
        qtbot.addWidget(form)
        duration = time_module.time() - start

        # El formulario debe cargar en menos de 1 segundo
        assert duration < 1.0, f"Carga demasiado lenta: {duration:.2f}s"

    def test_recarga_rapida(self, qtbot, session, config_completa):
        """Test: Recargar la configuración debe ser rápido."""
        import time as time_module

        form = ConfiguracionForm(session)
        qtbot.addWidget(form)

        start = time_module.time()
        form.cargar_configuracion()
        duration = time_module.time() - start

        # Recargar debe ser muy rápido (<200ms)
        assert duration < 0.2, f"Recarga demasiado lenta: {duration:.2f}s"
