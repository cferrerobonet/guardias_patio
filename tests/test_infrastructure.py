"""
Tests de ejemplo para verificar infraestructura de testing.

Estos tests simples verifican que pytest, fixtures y mocks funcionan correctamente.
"""

from datetime import date

import pytest


class TestInfraestructura:
    """Tests básicos de infraestructura."""

    def test_pytest_funciona(self):
        """Verificar que pytest está funcionando."""
        assert True

    def test_fixture_session(self, session):
        """Verificar que la fixture de sesión funciona."""
        assert session is not None
        # La sesión debe estar vacía al inicio
        from models.models import Profesor

        count = session.query(Profesor).count()
        assert count == 0

    def test_fixture_db_with_data(self, db_with_data):
        """Verificar que la fixture con datos funciona."""
        from models.models import Profesor, Zona

        # Debe tener 3 profesores
        profesores = db_with_data.query(Profesor).all()
        assert len(profesores) == 3

        # Debe tener 3 zonas
        zonas = db_with_data.query(Zona).all()
        assert len(zonas) == 3

    def test_profesor_factory(self, profesor_factory):
        """Verificar que el factory de profesores funciona."""
        profesor = profesor_factory(
            nombre_completo="Test Factory", horas_contrato=20, porcentaje_jornada=80
        )

        assert profesor.id is not None
        assert profesor.nombre_completo == "Test Factory"
        assert profesor.horas_contrato == 20
        assert profesor.porcentaje_jornada == 80

    def test_zona_factory(self, zona_factory):
        """Verificar que el factory de zonas funciona."""
        zona = zona_factory(nombre_zona="Zona Factory", descripcion="Test description")

        assert zona.id is not None
        assert zona.nombre_zona == "Zona Factory"
        assert zona.descripcion == "Test description"

    def test_guardia_factory(self, guardia_factory, profesor_factory, zona_factory):
        """Verificar que el factory de guardias funciona."""
        profesor = profesor_factory()
        zona = zona_factory()

        guardia = guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2025, 1, 15),
            turno="mañana",
            recreo=1,
        )

        assert guardia.id is not None
        assert guardia.profesor_id == profesor.id
        assert guardia.zona_id == zona.id
        assert guardia.fecha == date(2025, 1, 15)
        assert guardia.turno == "mañana"
        assert guardia.recreo == 1

    def test_ausencia_factory(self, ausencia_factory, profesor_factory):
        """Verificar que el factory de ausencias funciona."""
        profesor = profesor_factory()

        ausencia = ausencia_factory(
            profesor_id=profesor.id,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 5),
            tipo="permiso",
        )

        assert ausencia.id is not None
        assert ausencia.profesor_id == profesor.id
        assert ausencia.fecha_inicio == date(2025, 1, 1)
        assert ausencia.fecha_fin == date(2025, 1, 5)
        assert ausencia.tipo == "permiso"
        assert ausencia.activa is True

    def test_mock_session(self, mock_session):
        """Verificar que el mock de sesión funciona."""
        # Mock debe tener métodos de Session
        assert hasattr(mock_session, "query")
        assert hasattr(mock_session, "add")
        assert hasattr(mock_session, "commit")

    def test_sample_dates(self, sample_dates):
        """Verificar que las fechas de ejemplo funcionan."""
        assert "today" in sample_dates
        assert "tomorrow" in sample_dates
        assert "yesterday" in sample_dates
        assert "next_week" in sample_dates

        # Verificar que las fechas son correctas
        from datetime import timedelta

        assert sample_dates["tomorrow"] == sample_dates["today"] + timedelta(days=1)
        assert sample_dates["yesterday"] == sample_dates["today"] - timedelta(days=1)


@pytest.mark.ui
class TestQtInfraestructura:
    """Tests de infraestructura Qt."""

    def test_qapp_disponible(self, qapp):
        """Verificar que QApplication está disponible."""
        assert qapp is not None

    def test_qtbot_disponible(self, qtbot):
        """Verificar que qtbot está disponible."""
        assert qtbot is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
