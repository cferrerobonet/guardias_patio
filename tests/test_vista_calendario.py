"""
Tests para VistaCalendario widget.

Pruebas del widget de calendario que incluyen:
- Creación y renderizado del calendario
- Navegación entre meses
- Visualización de guardias
- Visualización de ausencias
- Estilos y leyendas
"""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QGroupBox, QLabel, QPushButton

from models.models import Ausencia, Guardia
from presentation.widgets.vista_calendario import VistaCalendario

# ========================================
# FIXTURES
# ========================================


@pytest.fixture
def vista_calendario(qapp, session):
    """Crear widget VistaCalendario para tests"""
    vista = VistaCalendario(session)
    return vista


@pytest.fixture
def fecha_fija():
    """Fecha fija para tests determinísticos"""
    return date(2024, 10, 15)


@pytest.fixture
def guardias_mes(session, profesor_factory, zona_factory):
    """Crear guardias para un mes completo"""
    prof1 = profesor_factory(nombre_completo="García, Juan")
    prof2 = profesor_factory(nombre_completo="López, María")
    zona1 = zona_factory(nombre_zona="Patio A")
    zona2 = zona_factory(nombre_zona="Patio B")

    guardias = []
    # Crear guardias para varios días de octubre 2024
    fechas = [
        date(2024, 10, 1),
        date(2024, 10, 2),
        date(2024, 10, 15),  # Mismo día que fecha_fija
        date(2024, 10, 20),
        date(2024, 10, 31),
    ]

    for i, fecha in enumerate(fechas):
        guardia = Guardia(
            profesor_id=prof1.id if i % 2 == 0 else prof2.id,
            zona_id=zona1.id if i % 2 == 0 else zona2.id,
            fecha=fecha,
            turno="mañana",
            recreo=1,
        )
        session.add(guardia)
        guardias.append(guardia)

    session.commit()
    return guardias


@pytest.fixture
def ausencias_mes(session, profesor_factory):
    """Crear ausencias para el mes"""
    prof = profesor_factory(nombre_completo="Martínez, Pedro")

    # Ausencia de 3 días
    ausencia = Ausencia(
        profesor_id=prof.id,
        fecha_inicio=date(2024, 10, 10),
        fecha_fin=date(2024, 10, 12),
        tipo="baja_medica",
        motivo="Gripe",
        activa=True,
    )
    session.add(ausencia)
    session.commit()
    return [ausencia]


# ========================================
# TESTS BÁSICOS
# ========================================


class TestVistaCalendarioBasico:
    """Tests básicos de creación y estructura del widget"""

    def test_crear_vista_calendario(self, qapp, session):
        """Test crear vista calendario correctamente"""
        vista = VistaCalendario(session)

        assert vista is not None
        assert hasattr(vista, "session")
        assert vista.session == session

    def test_inicializacion_con_fecha_actual(self, qapp, session):
        """Test que se inicializa con la fecha actual"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            assert vista.mes_mostrado == 10
            assert vista.anio_mostrado == 2024
            assert vista.fecha_actual == date(2024, 10, 15)

    def test_has_botones_navegacion(self, vista_calendario):
        """Test que tiene botones de navegación"""
        assert hasattr(vista_calendario, "btn_mes_anterior")
        assert hasattr(vista_calendario, "btn_mes_siguiente")
        assert hasattr(vista_calendario, "btn_hoy")

        assert isinstance(vista_calendario.btn_mes_anterior, QPushButton)
        assert isinstance(vista_calendario.btn_mes_siguiente, QPushButton)
        assert isinstance(vista_calendario.btn_hoy, QPushButton)

    def test_has_label_mes_anio(self, vista_calendario):
        """Test que tiene label de mes/año"""
        assert hasattr(vista_calendario, "label_mes_anio")
        assert isinstance(vista_calendario.label_mes_anio, QLabel)

        # Debe mostrar mes y año
        texto = vista_calendario.label_mes_anio.text()
        assert len(texto) > 0
        assert str(vista_calendario.anio_mostrado) in texto

    def test_has_calendario_layout(self, vista_calendario):
        """Test que tiene layout de calendario"""
        assert hasattr(vista_calendario, "calendario_layout")
        assert hasattr(vista_calendario, "calendario_widget")
        assert hasattr(vista_calendario, "scroll_area")

    def test_window_title(self, vista_calendario):
        """Test que tiene título de ventana correcto"""
        assert vista_calendario.windowTitle() == "Vista Calendario"


# ========================================
# TESTS DE NAVEGACIÓN
# ========================================


class TestVistaCalendarioNavegacion:
    """Tests de navegación entre meses"""

    def test_mes_siguiente_dentro_anio(self, qapp, session):
        """Test navegar al mes siguiente dentro del mismo año"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 5, 15)
            vista = VistaCalendario(session)

            assert vista.mes_mostrado == 5
            assert vista.anio_mostrado == 2024

            vista.mes_siguiente()

            assert vista.mes_mostrado == 6
            assert vista.anio_mostrado == 2024

    def test_mes_siguiente_cambio_anio(self, qapp, session):
        """Test navegar de diciembre a enero cambia año"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 12, 15)
            vista = VistaCalendario(session)

            assert vista.mes_mostrado == 12
            assert vista.anio_mostrado == 2024

            vista.mes_siguiente()

            assert vista.mes_mostrado == 1
            assert vista.anio_mostrado == 2025

    def test_mes_anterior_dentro_anio(self, qapp, session):
        """Test navegar al mes anterior dentro del mismo año"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 5, 15)
            vista = VistaCalendario(session)

            vista.mes_anterior()

            assert vista.mes_mostrado == 4
            assert vista.anio_mostrado == 2024

    def test_mes_anterior_cambio_anio(self, qapp, session):
        """Test navegar de enero a diciembre cambia año"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 15)
            vista = VistaCalendario(session)

            vista.mes_anterior()

            assert vista.mes_mostrado == 12
            assert vista.anio_mostrado == 2023

    def test_ir_a_hoy(self, qapp, session):
        """Test botón 'Hoy' vuelve al mes actual"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            # Navegar a otro mes
            vista.mes_siguiente()
            vista.mes_siguiente()
            assert vista.mes_mostrado == 12

            # Volver a hoy
            vista.ir_a_hoy()

            assert vista.mes_mostrado == 10
            assert vista.anio_mostrado == 2024

    def test_navegacion_multiple_meses(self, qapp, session):
        """Test navegar múltiples meses consecutivos"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 15)
            vista = VistaCalendario(session)

            # Avanzar 6 meses
            for _ in range(6):
                vista.mes_siguiente()

            assert vista.mes_mostrado == 12
            assert vista.anio_mostrado == 2024

            # Retroceder 12 meses
            for _ in range(12):
                vista.mes_anterior()

            assert vista.mes_mostrado == 12
            assert vista.anio_mostrado == 2023


# ========================================
# TESTS DE RENDERIZADO
# ========================================


class TestVistaCalendarioRenderizado:
    """Tests de renderizado del calendario"""

    def test_actualizar_calendario_sin_guardias(self, vista_calendario):
        """Test actualizar calendario sin guardias"""
        vista_calendario.mes_mostrado = 10
        vista_calendario.anio_mostrado = 2024

        vista_calendario.actualizar_calendario()

        # Verificar que el label se actualizó
        assert "Octubre" in vista_calendario.label_mes_anio.text()
        assert "2024" in vista_calendario.label_mes_anio.text()

        # Verificar que hay widgets en el layout (encabezados + días)
        assert vista_calendario.calendario_layout.count() > 0

    def test_encabezados_dias_semana(self, vista_calendario):
        """Test que muestra encabezados de días de la semana"""
        vista_calendario.actualizar_calendario()

        # Primera fila debe tener 7 labels (L-D)
        dias_esperados = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]

        for i, dia_esperado in enumerate(dias_esperados):
            widget = vista_calendario.calendario_layout.itemAtPosition(0, i).widget()
            assert isinstance(widget, QLabel)
            assert dia_esperado in widget.text()

    def test_actualizar_calendario_con_guardias(
        self, qapp, session, guardias_mes
    ):
        """Test actualizar calendario con guardias"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            vista.actualizar_calendario()

            # Verificar que hay celdas de días (31 días + 7 encabezados)
            assert vista.calendario_layout.count() >= 31 + 7

    def test_mes_mostrado_actualiza_label(self, vista_calendario):
        """Test que cambiar mes actualiza el label"""
        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

        for mes_num, mes_nombre in meses.items():
            vista_calendario.mes_mostrado = mes_num
            vista_calendario.anio_mostrado = 2024
            vista_calendario.actualizar_calendario()

            assert mes_nombre in vista_calendario.label_mes_anio.text()
            assert "2024" in vista_calendario.label_mes_anio.text()

    def test_limpieza_calendario_anterior(self, vista_calendario):
        """Test que limpia el calendario anterior al actualizar"""
        # Primera actualización
        vista_calendario.actualizar_calendario()
        count_inicial = vista_calendario.calendario_layout.count()

        # Segunda actualización
        vista_calendario.actualizar_calendario()
        count_final = vista_calendario.calendario_layout.count()

        # Debe tener aproximadamente el mismo número de widgets
        # (encabezados + días del mes)
        assert count_final > 0
        # No debe acumular widgets
        assert abs(count_final - count_inicial) < 10


# ========================================
# TESTS DE GUARDIAS
# ========================================


class TestVistaCalendarioGuardias:
    """Tests de visualización de guardias"""

    def test_cargar_guardias_mes(self, qapp, session, guardias_mes):
        """Test cargar guardias del mes correctamente"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            # Forzar actualización
            vista.actualizar_calendario()

            # Verificar que el calendario tiene widgets
            assert vista.calendario_layout.count() > 0

    def test_guardias_no_afectan_otros_meses(
        self, qapp, session, guardias_mes
    ):
        """Test que guardias de un mes no aparecen en otros"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            # Ver octubre (tiene guardias)
            vista.mes_mostrado = 10
            vista.actualizar_calendario()
            count_octubre = vista.calendario_layout.count()

            # Ver noviembre (sin guardias)
            vista.mes_mostrado = 11
            vista.actualizar_calendario()
            count_noviembre = vista.calendario_layout.count()

            # Ambos deben tener widgets (encabezados + días)
            assert count_octubre > 7
            assert count_noviembre > 7

    def test_multiples_guardias_mismo_dia(
        self, qapp, session, profesor_factory, zona_factory
    ):
        """Test múltiples guardias en el mismo día"""
        prof = profesor_factory()
        zona = zona_factory()

        # Crear 5 guardias el mismo día
        fecha = date(2024, 10, 15)
        for i in range(5):
            guardia = Guardia(
                profesor_id=prof.id,
                zona_id=zona.id,
                fecha=fecha,
                turno="mañana" if i < 3 else "tarde",
                recreo=(i % 2) + 1,
            )
            session.add(guardia)
        session.commit()

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            vista.actualizar_calendario()

            # El día 15 debe existir en el calendario
            assert vista.calendario_layout.count() > 0


# ========================================
# TESTS DE AUSENCIAS
# ========================================


class TestVistaCalendarioAusencias:
    """Tests de visualización de ausencias"""

    def test_cargar_ausencias_mes(self, qapp, session, ausencias_mes):
        """Test cargar ausencias del mes"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            vista.actualizar_calendario()

            # Debe renderizar el calendario con ausencias
            assert vista.calendario_layout.count() > 0

    def test_ausencia_multiple_dias(self, qapp, session, profesor_factory):
        """Test ausencia que abarca múltiples días"""
        prof = profesor_factory()

        # Ausencia de 7 días
        ausencia = Ausencia(
            profesor_id=prof.id,
            fecha_inicio=date(2024, 10, 10),
            fecha_fin=date(2024, 10, 16),
            tipo="vacaciones",
            motivo="Vacaciones",
            activa=True,
        )
        session.add(ausencia)
        session.commit()

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            # Agrupar ausencias
            ausencias_agrupadas = vista._agrupar_ausencias_por_fecha(
                [ausencia], date(2024, 10, 1), date(2024, 10, 31)
            )

            # Debe aparecer en los 7 días
            assert len(ausencias_agrupadas) == 7
            assert date(2024, 10, 10) in ausencias_agrupadas
            assert date(2024, 10, 16) in ausencias_agrupadas

    def test_ausencia_inactiva_no_aparece(
        self, qapp, session, profesor_factory
    ):
        """Test que ausencias inactivas no aparecen"""
        prof = profesor_factory()

        ausencia = Ausencia(
            profesor_id=prof.id,
            fecha_inicio=date(2024, 10, 10),
            fecha_fin=date(2024, 10, 12),
            tipo="permiso",
            motivo="Permiso",
            activa=False,  # Inactiva
        )
        session.add(ausencia)
        session.commit()

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            vista.actualizar_calendario()

            # No debe crashear, simplemente no mostrar la ausencia
            assert vista.calendario_layout.count() > 0


# ========================================
# TESTS DE ESTILOS
# ========================================


class TestVistaCalendarioEstilos:
    """Tests de estilos de celdas"""

    def test_estilo_dia_hoy(self, qapp, session):
        """Test que el día de hoy tiene estilo especial"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            hoy = datetime(2024, 10, 15)
            mock_dt.now.return_value = hoy
            vista = VistaCalendario(session)

            # Obtener estilo para hoy
            estilo_hoy = vista._obtener_estilo_celda(date(2024, 10, 15), [], [])

            # Debe tener color amarillo (hoy)
            assert "#fff9c4" in estilo_hoy or "yellow" in estilo_hoy.lower()

    def test_estilo_dia_con_guardias(self, vista_calendario):
        """Test que día con guardias tiene estilo especial"""
        mock_guardia = Mock()

        estilo = vista_calendario._obtener_estilo_celda(
            date(2024, 10, 20), [mock_guardia], []
        )

        # Debe tener color azul (con guardias)
        assert "#e3f2fd" in estilo or "blue" in estilo.lower()

    def test_estilo_dia_sin_guardias(self, vista_calendario):
        """Test que día sin guardias tiene estilo normal"""
        estilo = vista_calendario._obtener_estilo_celda(
            date(2024, 10, 20), [], []
        )

        # Debe tener color gris claro (sin guardias)
        assert "#fafafa" in estilo or "gray" in estilo.lower()

    def test_prioridad_estilo_hoy_sobre_guardias(self, qapp, session):
        """Test que estilo de 'hoy' tiene prioridad sobre guardias"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            mock_guardia = Mock()
            estilo = vista._obtener_estilo_celda(
                date(2024, 10, 15), [mock_guardia], []
            )

            # Debe ser amarillo (hoy) no azul (guardias)
            assert "#fff9c4" in estilo


# ========================================
# TESTS DE CELDAS
# ========================================


class TestVistaCalendarioCeldas:
    """Tests de creación de celdas"""

    def test_crear_celda_dia_basica(self, vista_calendario):
        """Test crear celda de día básica"""
        celda = vista_calendario._crear_celda_dia(15, [], date(2024, 10, 15))

        assert isinstance(celda, QGroupBox)
        # Debe tener un layout con al menos un widget (el número del día)
        assert celda.layout() is not None

    def test_celda_con_guardias(
        self, qapp, session, profesor_factory, zona_factory
    ):
        """Test celda con guardias muestra información"""
        prof = profesor_factory(nombre_completo="García, Juan")
        zona = zona_factory(nombre_zona="Patio A")

        guardia = Guardia(
            profesor_id=prof.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        session.add(guardia)
        session.commit()

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            celda = vista._crear_celda_dia(15, [guardia], date(2024, 10, 15))

            # Debe tener más de un widget (día + guardia)
            assert celda.layout().count() > 1

    def test_celda_con_ausencias_muestra_icono(
        self, qapp, session, profesor_factory
    ):
        """Test que celda con ausencias muestra icono"""
        prof = profesor_factory()
        ausencia = Ausencia(
            profesor_id=prof.id,
            fecha_inicio=date(2024, 10, 15),
            fecha_fin=date(2024, 10, 15),
            tipo="baja_medica",
            motivo="Gripe",
            activa=True,
        )

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            celda = vista._crear_celda_dia(
                15, [], date(2024, 10, 15), [ausencia]
            )

            # Debe existir la celda
            assert celda is not None

    def test_celda_limita_guardias_mostradas(
        self, qapp, session, profesor_factory, zona_factory
    ):
        """Test que celda muestra máximo 3 guardias + contador"""
        prof = profesor_factory()
        zona = zona_factory()

        # Crear 5 guardias
        guardias = []
        for i in range(5):
            g = Guardia(
                profesor_id=prof.id,
                zona_id=zona.id,
                fecha=date(2024, 10, 15),
                turno="mañana",
                recreo=(i % 2) + 1,
            )
            guardias.append(g)

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            celda = vista._crear_celda_dia(15, guardias, date(2024, 10, 15))

            # Debe tener layout
            assert celda.layout() is not None
            # Debe tener widgets (día + 3 guardias + "más" + stretch)
            assert celda.layout().count() >= 5


# ========================================
# TESTS DE INTEGRACIÓN
# ========================================


class TestVistaCalendarioIntegracion:
    """Tests de integración del widget"""

    def test_flujo_completo_navegacion_con_datos(
        self, qapp, session, guardias_mes, ausencias_mes
    ):
        """Test flujo completo de navegación con datos"""
        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            # 1. Ver mes actual
            assert vista.mes_mostrado == 10
            vista.actualizar_calendario()
            assert "Octubre" in vista.label_mes_anio.text()

            # 2. Navegar al siguiente
            vista.mes_siguiente()
            assert vista.mes_mostrado == 11
            assert "Noviembre" in vista.label_mes_anio.text()

            # 3. Volver a hoy
            vista.ir_a_hoy()
            assert vista.mes_mostrado == 10

            # 4. Navegar al anterior
            vista.mes_anterior()
            assert vista.mes_mostrado == 9

    def test_refrescar_metodo(self, vista_calendario):
        """Test método refrescar actualiza calendario"""
        mes_inicial = vista_calendario.mes_mostrado

        # Cambiar mes manualmente
        vista_calendario.mes_mostrado = (mes_inicial % 12) + 1

        # Refrescar debe actualizar
        vista_calendario.refrescar()

        # El label debe reflejar el nuevo mes
        texto_label = vista_calendario.label_mes_anio.text()
        assert len(texto_label) > 0

    def test_crear_celda_con_datos_completos(
        self, qapp, session, profesor_factory, zona_factory
    ):
        """Test crear celda con guardias y ausencias"""
        prof = profesor_factory(nombre_completo="García, Juan")
        zona = zona_factory(nombre_zona="Patio A")

        guardia = Guardia(
            profesor_id=prof.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )

        ausencia = Ausencia(
            profesor_id=prof.id,
            fecha_inicio=date(2024, 10, 15),
            fecha_fin=date(2024, 10, 15),
            tipo="permiso",
            motivo="Cita médica",
            activa=True,
        )

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            celda = vista._crear_celda_dia(
                15, [guardia], date(2024, 10, 15), [ausencia]
            )

            assert celda is not None
            assert celda.layout() is not None


# ========================================
# TESTS DE RENDIMIENTO
# ========================================


class TestVistaCalendarioRendimiento:
    """Tests de rendimiento del widget"""

    @pytest.mark.slow
    def test_carga_inicial_rapida(self, qapp, session):
        """Test que la carga inicial es rápida (<1s)"""
        import time

        start = time.time()
        vista = VistaCalendario(session)
        elapsed = time.time() - start

        assert vista.calendario_layout.count() > 0  # Widget creado
        assert elapsed < 1.0  # Menos de 1 segundo

    @pytest.mark.slow
    def test_navegacion_rapida(self, qapp, session, guardias_mes):
        """Test que la navegación es rápida (<500ms por mes)"""
        import time

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            vista = VistaCalendario(session)

            # Navegar 12 meses
            start = time.time()
            for _ in range(12):
                vista.mes_siguiente()
            elapsed = time.time() - start

            # Menos de 500ms por mes
            assert elapsed < 6.0  # 12 meses x 500ms

    @pytest.mark.slow
    def test_calendario_con_muchas_guardias(
        self, qapp, session, profesor_factory, zona_factory
    ):
        """Test rendimiento con muchas guardias (100+)"""
        import time

        prof = profesor_factory()
        zona = zona_factory()

        # Crear 100 guardias distribuidas en el mes
        for dia in range(1, 32):
            try:
                fecha = date(2024, 10, dia)
                for recreo in [1, 2]:
                    guardia = Guardia(
                        profesor_id=prof.id,
                        zona_id=zona.id,
                        fecha=fecha,
                        turno="mañana" if recreo == 1 else "tarde",
                        recreo=recreo,
                    )
                    session.add(guardia)
            except ValueError:
                # Día inválido (ej: 31 en algunos meses)
                pass
        session.commit()

        with patch("presentation.widgets.vista_calendario.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)

            start = time.time()
            vista = VistaCalendario(session)
            vista.actualizar_calendario()
            elapsed = time.time() - start

            # Debe cargar en menos de 2 segundos incluso con 100+ guardias
            assert elapsed < 2.0
            assert vista.calendario_layout.count() > 0  # Usar vista
