"""
Tests para el sistema multicurso.

Valida que el sistema de múltiples cursos escolares funciona correctamente:
- CRUD de cursos
- Activación/desactivación de cursos
- Filtrado de guardias por curso
- Filtrado de profesores por curso
- Aislamiento de datos entre cursos
- Integridad referencial
"""

from datetime import date

import pytest
from models.models import CursoEscolar, Guardia, Profesor, Zona
from services.gestor_cursos import GestorCursos
from sqlalchemy.orm import Session

# ============================================================================
# FIXTURES ESPECÍFICAS PARA MULTICURSO
# ============================================================================


@pytest.fixture
def curso_2024_2025(session: Session) -> CursoEscolar:
    """Fixture: Curso escolar 2024/2025 (inactivo)."""
    curso = CursoEscolar(
        nombre="2024/2025",
        fecha_inicio=date(2024, 9, 8),
        fecha_fin=date(2025, 6, 20),
        activo=False,
    )
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso


@pytest.fixture
def curso_2025_2026(session: Session) -> CursoEscolar:
    """Fixture: Curso escolar 2025/2026 (activo)."""
    curso = CursoEscolar(
        nombre="2025/2026",
        fecha_inicio=date(2025, 9, 8),
        fecha_fin=date(2026, 6, 20),
        activo=True,
    )
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso


@pytest.fixture
def curso_2026_2027(session: Session) -> CursoEscolar:
    """Fixture: Curso escolar 2026/2027 (inactivo)."""
    curso = CursoEscolar(
        nombre="2026/2027",
        fecha_inicio=date(2026, 9, 8),
        fecha_fin=date(2027, 6, 20),
        activo=False,
    )
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso


@pytest.fixture
def profesores_con_guardias(
    session: Session,
    curso_2024_2025: CursoEscolar,
    curso_2025_2026: CursoEscolar,
) -> tuple[Profesor, Profesor]:
    """Fixture: Dos profesores con guardias en diferentes cursos."""
    # Crear profesores
    prof1 = Profesor(
        nombre_completo="García López, Juan",
        horas_contrato=30.0,
        porcentaje_jornada=100,
        turno="mañana",
        activo=True,
    )
    prof2 = Profesor(
        nombre_completo="Martínez Ruiz, Ana",
        horas_contrato=30.0,
        porcentaje_jornada=100,
        turno="tarde",
        activo=True,
    )
    session.add_all([prof1, prof2])
    session.commit()

    # Crear zonas
    zona1 = Zona(nombre="Patio A")
    zona2 = Zona(nombre="Patio B")
    session.add_all([zona1, zona2])
    session.commit()

    # Crear guardias para curso 2024/2025
    guardia1 = Guardia(
        curso_id=curso_2024_2025.id,
        profesor_id=prof1.id,
        fecha=date(2024, 10, 15),
        turno="mañana",
        recreo=1,
        zona_id=zona1.id,
    )
    guardia2 = Guardia(
        curso_id=curso_2024_2025.id,
        profesor_id=prof2.id,
        fecha=date(2024, 10, 16),
        turno="tarde",
        recreo=2,
        zona_id=zona2.id,
    )

    # Crear guardias para curso 2025/2026
    guardia3 = Guardia(
        curso_id=curso_2025_2026.id,
        profesor_id=prof1.id,
        fecha=date(2025, 10, 15),
        turno="mañana",
        recreo=1,
        zona_id=zona1.id,
    )
    guardia4 = Guardia(
        curso_id=curso_2025_2026.id,
        profesor_id=prof2.id,
        fecha=date(2025, 10, 16),
        turno="tarde",
        recreo=2,
        zona_id=zona2.id,
    )

    session.add_all([guardia1, guardia2, guardia3, guardia4])
    session.commit()

    return prof1, prof2


# ============================================================================
# TESTS: CRUD DE CURSOS
# ============================================================================


class TestCRUDCursos:
    """Tests para operaciones CRUD de cursos escolares."""

    def test_crear_curso(self, session: Session):
        """Test: Crear un nuevo curso escolar."""
        # Arrange
        nombre = "2027/2028"
        fecha_inicio = date(2027, 9, 8)
        fecha_fin = date(2028, 6, 20)

        # Act
        curso = GestorCursos.crear_curso(session, nombre, fecha_inicio, fecha_fin)

        # Assert
        assert curso is not None
        assert curso.id is not None
        assert curso.nombre == nombre
        assert curso.fecha_inicio == fecha_inicio
        assert curso.fecha_fin == fecha_fin
        assert curso.activo is False  # Por defecto inactivo
        assert curso.cerrado is False

    def test_crear_curso_duplicado(self, session: Session, curso_2025_2026: CursoEscolar):
        """Test: No se puede crear curso con nombre duplicado."""
        # Act & Assert
        with pytest.raises(ValueError, match="ya existe"):
            GestorCursos.crear_curso(
                session,
                curso_2025_2026.nombre,
                date(2025, 9, 1),
                date(2026, 6, 30),
            )

    def test_listar_cursos(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
    ):
        """Test: Listar todos los cursos."""
        # Act
        cursos = GestorCursos.listar_todos_cursos(session, incluir_cerrados=False)

        # Assert
        assert len(cursos) == 2
        nombres = [c.nombre for c in cursos]
        assert "2024/2025" in nombres
        assert "2025/2026" in nombres

    def test_listar_cursos_incluir_cerrados(self, session: Session):
        """Test: Listar cursos incluyendo cerrados."""
        # Arrange
        curso1 = GestorCursos.crear_curso(session, "2023/2024", date(2023, 9, 1), date(2024, 6, 30))
        GestorCursos.cerrar_curso(session, curso1.id)

        GestorCursos.crear_curso(session, "2024/2025", date(2024, 9, 1), date(2025, 6, 30))

        # Act
        cursos_todos = GestorCursos.listar_todos_cursos(session, incluir_cerrados=True)
        cursos_activos = GestorCursos.listar_todos_cursos(session, incluir_cerrados=False)

        # Assert
        assert len(cursos_todos) == 2
        assert len(cursos_activos) == 1
        assert cursos_activos[0].nombre == "2024/2025"

    def test_obtener_curso_por_id(self, session: Session, curso_2025_2026: CursoEscolar):
        """Test: Obtener curso por ID."""
        # Act
        curso = GestorCursos.obtener_curso(session, curso_2025_2026.id)

        # Assert
        assert curso is not None
        assert curso.id == curso_2025_2026.id
        assert curso.nombre == curso_2025_2026.nombre

    def test_obtener_curso_inexistente(self, session: Session):
        """Test: Obtener curso inexistente retorna None."""
        # Act
        curso = GestorCursos.obtener_curso(session, 99999)

        # Assert
        assert curso is None

    def test_eliminar_curso_sin_guardias(self, session: Session):
        """Test: Eliminar curso que no tiene guardias."""
        # Arrange
        curso = GestorCursos.crear_curso(session, "2030/2031", date(2030, 9, 1), date(2031, 6, 30))

        # Act
        resultado = GestorCursos.eliminar_curso(session, curso.id)

        # Assert
        assert resultado is True
        curso_eliminado = GestorCursos.obtener_curso(session, curso.id)
        assert curso_eliminado is None

    def test_eliminar_curso_con_guardias(
        self,
        session: Session,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: No se puede eliminar curso con guardias asignadas."""
        # Act & Assert
        with pytest.raises(ValueError, match="tiene guardias"):
            GestorCursos.eliminar_curso(session, curso_2025_2026.id)


# ============================================================================
# TESTS: ACTIVACIÓN Y CIERRE DE CURSOS
# ============================================================================


class TestActivacionCursos:
    """Tests para activación y cierre de cursos."""

    def test_activar_curso(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
    ):
        """Test: Activar un curso desactiva todos los demás."""
        # Arrange
        assert curso_2025_2026.activo is True
        assert curso_2024_2025.activo is False

        # Act
        GestorCursos.activar_curso(session, curso_2024_2025.id)

        # Assert
        session.refresh(curso_2024_2025)
        session.refresh(curso_2025_2026)
        assert curso_2024_2025.activo is True
        assert curso_2025_2026.activo is False

    def test_obtener_curso_activo(self, session: Session, curso_2025_2026: CursoEscolar):
        """Test: Obtener el curso activo."""
        # Act
        curso_activo = GestorCursos.obtener_curso_activo(session)

        # Assert
        assert curso_activo is not None
        assert curso_activo.id == curso_2025_2026.id
        assert curso_activo.activo is True

    def test_obtener_curso_activo_sin_cursos(self, session: Session):
        """Test: Si no hay cursos activos, retorna None."""
        # Act
        curso_activo = GestorCursos.obtener_curso_activo(session)

        # Assert
        assert curso_activo is None

    def test_cerrar_curso(self, session: Session, curso_2025_2026: CursoEscolar):
        """Test: Cerrar un curso lo marca como cerrado."""
        # Act
        resultado = GestorCursos.cerrar_curso(session, curso_2025_2026.id)

        # Assert
        assert resultado is True
        session.refresh(curso_2025_2026)
        assert curso_2025_2026.cerrado is True

    def test_no_cerrar_curso_activo(
        self,
        session: Session,
        curso_2025_2026: CursoEscolar,
    ):
        """Test: No se puede cerrar el curso activo."""
        # Act & Assert
        with pytest.raises(ValueError, match="curso activo"):
            GestorCursos.cerrar_curso(session, curso_2025_2026.id)


# ============================================================================
# TESTS: FILTRADO DE GUARDIAS POR CURSO
# ============================================================================


class TestFiltradoGuardias:
    """Tests para verificar filtrado de guardias por curso."""

    def test_guardias_filtradas_por_curso_activo(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Solo se obtienen guardias del curso activo."""
        # Arrange
        curso_activo = GestorCursos.obtener_curso_activo(session)
        assert curso_activo.id == curso_2025_2026.id

        # Act
        guardias = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_activo.id)
            .all()
        )

        # Assert
        assert len(guardias) == 2
        for guardia in guardias:
            assert guardia.curso_id == curso_activo.id
            assert guardia.fecha.year == 2025

    def test_guardias_por_profesor_y_curso(
        self,
        session: Session,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Filtrar guardias por profesor y curso."""
        # Arrange
        prof1, prof2 = profesores_con_guardias

        # Act
        guardias_prof1 = (
            session.query(Guardia)
            .filter(
                Guardia.profesor_id == prof1.id,
                Guardia.curso_id == curso_2025_2026.id,
            )
            .all()
        )

        # Assert
        assert len(guardias_prof1) == 1
        assert guardias_prof1[0].profesor_id == prof1.id
        assert guardias_prof1[0].curso_id == curso_2025_2026.id

    def test_contar_guardias_por_curso(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Contar guardias de cada curso."""
        # Act
        count_2024 = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2024_2025.id)
            .count()
        )
        count_2025 = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2025_2026.id)
            .count()
        )

        # Assert
        assert count_2024 == 2
        assert count_2025 == 2


# ============================================================================
# TESTS: AISLAMIENTO DE DATOS ENTRE CURSOS
# ============================================================================


class TestAislamientoDatos:
    """Tests para verificar que los datos de un curso no afectan a otros."""

    def test_profesores_distintos_en_diferentes_cursos(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Los profesores con guardias se identifican por curso."""
        # Act: Obtener profesores con guardias en cada curso
        profesores_2024 = (
            session.query(Profesor)
            .join(Guardia)
            .filter(Guardia.curso_id == curso_2024_2025.id)
            .distinct()
            .all()
        )

        profesores_2025 = (
            session.query(Profesor)
            .join(Guardia)
            .filter(Guardia.curso_id == curso_2025_2026.id)
            .distinct()
            .all()
        )

        # Assert: Ambos cursos tienen los mismos 2 profesores
        assert len(profesores_2024) == 2
        assert len(profesores_2025) == 2

    def test_cambiar_curso_activo_no_afecta_guardias(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Cambiar curso activo no modifica las guardias existentes."""
        # Arrange
        guardias_2025_antes = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2025_2026.id)
            .count()
        )
        guardias_2024_antes = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2024_2025.id)
            .count()
        )

        # Act: Cambiar curso activo
        GestorCursos.activar_curso(session, curso_2024_2025.id)

        # Assert: Las guardias siguen igual
        guardias_2025_despues = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2025_2026.id)
            .count()
        )
        guardias_2024_despues = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2024_2025.id)
            .count()
        )

        assert guardias_2025_antes == guardias_2025_despues
        assert guardias_2024_antes == guardias_2024_despues

    def test_eliminar_guardias_solo_afecta_curso_especifico(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Eliminar guardias de un curso no afecta a otros."""
        # Arrange
        guardias_2025_antes = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2025_2026.id)
            .count()
        )

        # Act: Eliminar guardias del curso 2024/2025
        session.query(Guardia).filter(
            Guardia.curso_id == curso_2024_2025.id
        ).delete()
        session.commit()

        # Assert
        guardias_2024_despues = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2024_2025.id)
            .count()
        )
        guardias_2025_despues = (
            session.query(Guardia)
            .filter(Guardia.curso_id == curso_2025_2026.id)
            .count()
        )

        assert guardias_2024_despues == 0
        assert guardias_2025_despues == guardias_2025_antes


# ============================================================================
# TESTS: INTEGRIDAD REFERENCIAL
# ============================================================================


class TestIntegridadReferencial:
    """Tests para verificar integridad referencial del sistema."""

    def test_guardia_requiere_curso_id(self, session: Session):
        """Test: Una guardia debe tener curso_id (puede ser NULL por migración)."""
        # Arrange
        profesor = Profesor(
            nombre_completo="Test Profesor",
            horas_contrato=30.0,
            porcentaje_jornada=100,
            turno="mañana",
            activo=True,
        )
        zona = Zona(nombre="Test Zona")
        session.add_all([profesor, zona])
        session.commit()

        # Act: Crear guardia sin curso_id (permitido por nullable=True)
        guardia = Guardia(
            curso_id=None,  # NULL permitido para migración gradual
            profesor_id=profesor.id,
            fecha=date(2025, 10, 15),
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()

        # Assert: Se crea correctamente (por compatibilidad)
        assert guardia.id is not None
        assert guardia.curso_id is None

    def test_guardia_con_curso_invalido(self, session: Session):
        """Test: No se puede crear guardia con curso_id que no existe."""
        # Arrange
        profesor = Profesor(
            nombre_completo="Test Profesor",
            horas_contrato=30.0,
            porcentaje_jornada=100,
            turno="mañana",
            activo=True,
        )
        zona = Zona(nombre="Test Zona")
        session.add_all([profesor, zona])
        session.commit()

        # Act & Assert
        guardia = Guardia(
            curso_id=99999,  # ID que no existe
            profesor_id=profesor.id,
            fecha=date(2025, 10, 15),
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add(guardia)

        with pytest.raises(Exception):  # SQLAlchemy lanzará error de FK
            session.commit()

    def test_relacion_curso_guardias(
        self,
        session: Session,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Relación bidireccional entre Curso y Guardias."""
        # Act
        guardias_del_curso = curso_2025_2026.guardias

        # Assert
        assert len(guardias_del_curso) == 2
        for guardia in guardias_del_curso:
            assert guardia.curso_id == curso_2025_2026.id
            assert guardia.curso.nombre == "2025/2026"


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================


class TestIntegracionMulticurso:
    """Tests de integración para flujos completos multicurso."""

    def test_flujo_completo_nuevo_curso(self, session: Session):
        """Test: Flujo completo de crear y usar un nuevo curso."""
        # 1. Crear curso
        curso = GestorCursos.crear_curso(
            session,
            "2028/2029",
            date(2028, 9, 8),
            date(2029, 6, 20),
        )
        assert curso.activo is False

        # 2. Activar curso
        GestorCursos.activar_curso(session, curso.id)
        session.refresh(curso)
        assert curso.activo is True

        # 3. Crear datos para el curso
        profesor = Profesor(
            nombre_completo="Nuevo Profesor",
            horas_contrato=30.0,
            porcentaje_jornada=100,
            turno="mañana",
            activo=True,
        )
        zona = Zona(nombre="Nueva Zona")
        session.add_all([profesor, zona])
        session.commit()

        # 4. Crear guardias para el curso
        guardia = Guardia(
            curso_id=curso.id,
            profesor_id=profesor.id,
            fecha=date(2028, 10, 15),
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()

        # 5. Verificar que las guardias están asociadas
        guardias = session.query(Guardia).filter(Guardia.curso_id == curso.id).all()
        assert len(guardias) == 1
        assert guardias[0].profesor_id == profesor.id

        # 6. Cerrar curso
        GestorCursos.activar_curso(session, 0)  # Desactivar todos
        GestorCursos.cerrar_curso(session, curso.id)
        session.refresh(curso)
        assert curso.cerrado is True

    def test_estadisticas_por_curso(
        self,
        session: Session,
        curso_2024_2025: CursoEscolar,
        curso_2025_2026: CursoEscolar,
        profesores_con_guardias,
    ):
        """Test: Estadísticas se calculan correctamente por curso."""
        prof1, prof2 = profesores_con_guardias

        # Estadísticas curso 2024/2025
        guardias_prof1_2024 = (
            session.query(Guardia)
            .filter(
                Guardia.profesor_id == prof1.id,
                Guardia.curso_id == curso_2024_2025.id,
            )
            .count()
        )

        # Estadísticas curso 2025/2026
        guardias_prof1_2025 = (
            session.query(Guardia)
            .filter(
                Guardia.profesor_id == prof1.id,
                Guardia.curso_id == curso_2025_2026.id,
            )
            .count()
        )

        # Assert
        assert guardias_prof1_2024 == 1
        assert guardias_prof1_2025 == 1
        # Las estadísticas son independientes por curso


# ============================================================================
# MARCADORES DE CATEGORÍAS
# ============================================================================

pytestmark = pytest.mark.multicurso
