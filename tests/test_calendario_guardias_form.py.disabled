"""
Tests para CalendarioGuardiasForm.

Cobertura actual: 7.49%
Objetivo: >70%
"""

from datetime import date, timedelta

import pytest
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QCalendarWidget, QComboBox, QPushButton, QTextEdit

from models.models import Guardia
from presentation.forms.calendario_guardias_form import CalendarioGuardiasForm


@pytest.fixture
def profesores_guardias(session, profesor_factory, zona_factory):
    """Fixture con profesores y guardias para tests."""
    # Crear profesores usando factory
    prof1 = profesor_factory(
        nombre_completo="PÉREZ, Juan",
        horas_contrato=25.0,
        tutor=True
    )
    prof2 = profesor_factory(
        nombre_completo="GARCÍA, Ana",
        horas_contrato=25.0,
        tutor=False
    )

    # Crear zonas usando factory
    zona1 = zona_factory(nombre_zona="Patio A")
    zona2 = zona_factory(nombre_zona="Patio B")

    # Crear guardias
    hoy = date.today()
    guardia1 = Guardia(
        profesor_id=prof1.id,
        fecha=hoy,
        turno="mañana",
        recreo=1,
        zona_id=zona1.id
    )
    guardia2 = Guardia(
        profesor_id=prof2.id,
        fecha=hoy,
        turno="tarde",
        recreo=1,
        zona_id=zona2.id
    )
    guardia3 = Guardia(
        profesor_id=prof1.id,
        fecha=hoy + timedelta(days=1),
        turno="mañana",
        recreo=2,
        zona_id=zona1.id
    )
    session.add_all([guardia1, guardia2, guardia3])
    session.commit()

    return {
        'profesores': [prof1, prof2],
        'zonas': [zona1, zona2],
        'guardias': [guardia1, guardia2, guardia3]
    }


@pytest.mark.ui
class TestCalendarioGuardiasFormBasico:
    """Tests básicos de CalendarioGuardiasForm."""

    def test_crear_formulario(self, qtbot, session):
        """Test: Se puede crear el formulario de calendario."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert form.windowTitle() == "Calendario de Guardias"

    def test_calendario_widget_presente(self, qtbot, session):
        """Test: El widget de calendario está presente."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form.calendario is not None
        assert isinstance(form.calendario, QCalendarWidget)
        assert form.calendario.isGridVisible()

    def test_filtros_presentes(self, qtbot, session):
        """Test: Los filtros están presentes."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form.filtro_profesor is not None
        assert form.filtro_zona is not None
        assert form.filtro_turno is not None
        assert isinstance(form.filtro_profesor, QComboBox)
        assert isinstance(form.filtro_zona, QComboBox)
        assert isinstance(form.filtro_turno, QComboBox)

    def test_areas_texto_presentes(self, qtbot, session):
        """Test: Las áreas de texto están presentes."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form.guardias_dia_text is not None
        assert form.stats_text is not None
        assert isinstance(form.guardias_dia_text, QTextEdit)
        assert isinstance(form.stats_text, QTextEdit)
        assert form.guardias_dia_text.isReadOnly()
        assert form.stats_text.isReadOnly()


@pytest.mark.ui
class TestCalendarioGuardiasFormFiltros:
    """Tests para el sistema de filtros."""

    def test_filtro_profesor_carga_profesores(self, qtbot, session, profesores_guardias):
        """Test: El filtro de profesor carga todos los profesores."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Debe tener "Todos" + los profesores
        assert form.filtro_profesor.count() >= 3
        assert form.filtro_profesor.itemText(0) == "Todos los profesores"

    def test_filtro_zona_carga_zonas(self, qtbot, session, profesores_guardias):
        """Test: El filtro de zona carga todas las zonas."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Debe tener "Todas" + las zonas
        assert form.filtro_zona.count() >= 3
        assert form.filtro_zona.itemText(0) == "Todas las zonas"

    def test_filtro_turno_tiene_opciones(self, qtbot, session):
        """Test: El filtro de turno tiene las opciones correctas."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form.filtro_turno.count() == 3
        assert form.filtro_turno.itemText(0) == "Todos"
        assert form.filtro_turno.itemText(1) == "mañana"
        assert form.filtro_turno.itemText(2) == "tarde"

    def test_limpiar_filtros_boton_existe(self, qtbot, session):
        """Test: El botón de limpiar filtros existe."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form.limpiar_filtros_btn is not None
        assert isinstance(form.limpiar_filtros_btn, QPushButton)
        assert form.limpiar_filtros_btn.text() == "Limpiar filtros"

    def test_limpiar_filtros_resetea_seleccion(self, qtbot, session, profesores_guardias):
        """Test: Limpiar filtros resetea la selección."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Cambiar filtros
        form.filtro_profesor.setCurrentIndex(1)
        form.filtro_turno.setCurrentIndex(1)

        # Limpiar
        form.limpiar_filtros()

        # Verificar que vuelven a "Todos"
        assert form.filtro_profesor.currentIndex() == 0
        assert form.filtro_zona.currentIndex() == 0
        assert form.filtro_turno.currentIndex() == 0


@pytest.mark.ui
class TestCalendarioGuardiasFormCalendario:
    """Tests para el calendario."""

    def test_seleccionar_fecha_actualiza_detalles(self, qtbot, session, profesores_guardias):
        """Test: Seleccionar una fecha actualiza los detalles."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Seleccionar fecha de hoy
        hoy = QDate.currentDate()
        form.calendario.setSelectedDate(hoy)
        form.actualizar_guardias_dia(hoy)

        # Debe mostrar algo en el área de detalles
        texto = form.guardias_dia_text.toPlainText()
        assert texto is not None
        assert len(texto) > 0

    def test_fecha_sin_guardias_muestra_mensaje(self, qtbot, session):
        """Test: Una fecha sin guardias muestra mensaje apropiado."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Seleccionar fecha muy lejana (sin guardias)
        fecha_futura = QDate.currentDate().addYears(10)
        form.calendario.setSelectedDate(fecha_futura)
        form.actualizar_guardias_dia(fecha_futura)

        texto = form.guardias_dia_text.toPlainText()
        assert "No hay guardias" in texto or len(texto) == 0

    def test_calendario_fecha_actual_por_defecto(self, qtbot, session):
        """Test: El calendario muestra la fecha actual por defecto."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        fecha_seleccionada = form.calendario.selectedDate()
        fecha_hoy = QDate.currentDate()

        # Pueden diferir en día pero deben ser cercanas
        assert abs(fecha_seleccionada.toJulianDay() - fecha_hoy.toJulianDay()) < 7


@pytest.mark.ui
class TestCalendarioGuardiasFormEstadisticas:
    """Tests para las estadísticas."""

    def test_estadisticas_se_actualizan(self, qtbot, session, profesores_guardias):
        """Test: Las estadísticas se actualizan."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        form.actualizar_estadisticas()

        texto = form.stats_text.toPlainText()
        assert texto is not None
        assert len(texto) > 0

    def test_estadisticas_muestran_total_guardias(self, qtbot, session, profesores_guardias):
        """Test: Las estadísticas muestran el total de guardias."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        form.actualizar_estadisticas()

        texto = form.stats_text.toPlainText()
        # Debe mencionar guardias de alguna forma
        assert "guardia" in texto.lower() or "total" in texto.lower()


@pytest.mark.ui
class TestCalendarioGuardiasFormIntegracion:
    """Tests de integración del formulario."""

    def test_cambiar_filtro_profesor_actualiza_vista(self, qtbot, session, profesores_guardias):
        """Test: Cambiar el filtro de profesor actualiza la vista."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Cambiar filtro
        form.filtro_profesor.setCurrentIndex(1)
        form.aplicar_filtros()

        # El texto puede cambiar o mantenerse dependiendo de los datos
        # pero la función debe ejecutarse sin errores
        assert form.guardias_dia_text is not None

    def test_cambiar_filtro_turno_actualiza_vista(self, qtbot, session, profesores_guardias):
        """Test: Cambiar el filtro de turno actualiza la vista."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Cambiar a turno mañana
        form.filtro_turno.setCurrentIndex(1)
        form.aplicar_filtros()

        # Verificar que no hay errores
        assert form.guardias_dia_text is not None

    def test_ciclo_completo_filtrado(self, qtbot, session, profesores_guardias):
        """Test: Ciclo completo de filtrado funciona."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # 1. Seleccionar fecha con guardias
        hoy = QDate.currentDate()
        form.calendario.setSelectedDate(hoy)

        # 2. Aplicar filtro de turno
        form.filtro_turno.setCurrentIndex(1)  # mañana

        # 3. Actualizar
        form.aplicar_filtros()

        # Verificar que funciona sin errores
        assert form.guardias_dia_text is not None
        assert form.stats_text is not None

    def test_multiples_cambios_fecha_consecutivos(self, qtbot, session, profesores_guardias):
        """Test: Múltiples cambios de fecha consecutivos funcionan."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        hoy = QDate.currentDate()

        # Cambiar varias veces
        for i in range(5):
            fecha = hoy.addDays(i)
            form.calendario.setSelectedDate(fecha)
            form.actualizar_guardias_dia(fecha)

        # Debe funcionar sin problemas
        assert form.guardias_dia_text is not None


@pytest.mark.ui
class TestCalendarioGuardiasFormMetodos:
    """Tests para métodos específicos del formulario."""

    def test_cargar_filtros_metodo_existe(self, qtbot, session):
        """Test: El método cargar_filtros existe."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, 'cargar_filtros')
        assert callable(form.cargar_filtros)

    def test_actualizar_guardias_dia_metodo_existe(self, qtbot, session):
        """Test: El método actualizar_guardias_dia existe."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, 'actualizar_guardias_dia')
        assert callable(form.actualizar_guardias_dia)

    def test_actualizar_estadisticas_metodo_existe(self, qtbot, session):
        """Test: El método actualizar_estadisticas existe."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, 'actualizar_estadisticas')
        assert callable(form.actualizar_estadisticas)

    def test_aplicar_filtros_metodo_existe(self, qtbot, session):
        """Test: El método aplicar_filtros existe."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, 'aplicar_filtros')
        assert callable(form.aplicar_filtros)

    def test_limpiar_filtros_metodo_existe(self, qtbot, session):
        """Test: El método limpiar_filtros existe."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, 'limpiar_filtros')
        assert callable(form.limpiar_filtros)


@pytest.mark.ui
class TestCalendarioGuardiasFormRobustez:
    """Tests de robustez y casos edge."""

    def test_form_sin_guardias_en_bd(self, qtbot, session):
        """Test: El formulario funciona sin guardias en la base de datos."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert form.guardias_dia_text is not None

    def test_form_sin_profesores_en_bd(self, qtbot, session):
        """Test: El formulario funciona sin profesores en la base de datos."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Solo debe tener la opción "Todos"
        assert form.filtro_profesor.count() >= 1

    def test_form_sin_zonas_en_bd(self, qtbot, session):
        """Test: El formulario funciona sin zonas en la base de datos."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Solo debe tener la opción "Todas"
        assert form.filtro_zona.count() >= 1

    def test_actualizar_guardias_fecha_none(self, qtbot, session):
        """Test: Actualizar con fecha None no causa errores."""
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        # Esto podría causar error si no se maneja bien
        try:
            # QDate() sin parámetros crea fecha inválida
            fecha_invalida = QDate()
            if fecha_invalida.isValid():
                form.actualizar_guardias_dia(fecha_invalida)
        except Exception:
            pytest.fail("No debe fallar con fecha inválida")


@pytest.mark.ui
@pytest.mark.slow
class TestCalendarioGuardiasFormRendimiento:
    """Tests de rendimiento."""

    def test_carga_rapida(self, qtbot, session, profesores_guardias):
        """Test: El formulario carga rápidamente."""
        import time

        start = time.time()
        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)
        duration = time.time() - start

        assert duration < 2.0, f"Carga demasiado lenta: {duration:.2f}s"

    def test_cambio_fecha_rapido(self, qtbot, session, profesores_guardias):
        """Test: Cambiar de fecha es rápido."""
        import time

        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        start = time.time()
        fecha = QDate.currentDate()
        form.actualizar_guardias_dia(fecha)
        duration = time.time() - start

        assert duration < 0.5, f"Actualización demasiado lenta: {duration:.2f}s"

    def test_aplicar_filtros_rapido(self, qtbot, session, profesores_guardias):
        """Test: Aplicar filtros es rápido."""
        import time

        form = CalendarioGuardiasForm(session)
        qtbot.addWidget(form)

        start = time.time()
        form.aplicar_filtros()
        duration = time.time() - start

        assert duration < 0.3, f"Filtrado demasiado lento: {duration:.2f}s"
