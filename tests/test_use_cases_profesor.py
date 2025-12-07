"""
Tests para Use Cases de Profesor

Tests unitarios y de integración para los casos de uso relacionados con profesores.
Cubre: Crear, Actualizar, Eliminar, Obtener, Listar, Buscar

Sprint 6 - Task 4.2: Use Cases Profesor
Target Coverage: >90% para cada Use Case
"""

from datetime import date

import pytest
from application.dtos import ActualizarProfesorDTO, CrearProfesorDTO, ProfesorDTO
from application.use_cases.profesor.actualizar_profesor import ActualizarProfesorUseCase
from application.use_cases.profesor.buscar_profesores import BuscarProfesoresUseCase
from application.use_cases.profesor.crear_profesor import CrearProfesorUseCase
from application.use_cases.profesor.eliminar_profesor import EliminarProfesorUseCase
from application.use_cases.profesor.listar_profesores import ListarProfesoresUseCase
from application.use_cases.profesor.obtener_profesor import ObtenerProfesorUseCase
from core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from sqlalchemy.orm import Session

# ============================
# Tests: CrearProfesorUseCase
# ============================


class TestCrearProfesorUseCase:
    """Tests para el caso de uso de crear profesor."""

    def test_crear_profesor_exitoso_completo(self, session: Session, profesor_factory):
        """Test: crear profesor con todos los campos incluyendo email."""
        use_case = CrearProfesorUseCase(session)

        dto = CrearProfesorDTO(
            nombre_completo="Juan Pérez García",
            email_corporativo="juan.perez@colegio.edu",
            horas_contrato=25.0,
            turno="mañana",
            tutor=True,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
            dias_semana_permitidos=[0, 1, 2, 3, 4],  # Lunes a Viernes
            recreos_permitidos=[1, 2],
        )

        resultado = use_case.execute(dto)

        assert resultado.id > 0
        assert resultado.nombre_completo == "Juan Pérez García"
        assert resultado.email_corporativo == "juan.perez@colegio.edu"
        assert resultado.horas_contrato == 25.0
        assert resultado.turno == "mañana"
        assert resultado.tutor is True
        assert resultado.dias_semana_permitidos == [0, 1, 2, 3, 4]

        # Verificar en BD - usar expire_all para refrescar objetos en cache
        session.expire_all()
        from infrastructure.database.models import Profesor

        profesor_bd = session.query(Profesor).filter_by(nombre_completo="Juan Pérez García").first()
        assert profesor_bd is not None
        assert profesor_bd.email_corporativo == "juan.perez@colegio.edu"

    def test_crear_profesor_sin_email(self, session: Session):
        """Test: crear profesor sin email corporativo (campo opcional)."""
        use_case = CrearProfesorUseCase(session)

        dto = CrearProfesorDTO(
            nombre_completo="María López",
            email_corporativo=None,  # Email opcional
            horas_contrato=18.0,
            turno="tarde",
            tutor=False,
        )

        resultado = use_case.execute(dto)

        assert resultado.id > 0
        assert resultado.nombre_completo == "María López"
        assert resultado.email_corporativo is None
        assert resultado.horas_contrato == 18.0
        assert resultado.turno == "tarde"

    def test_crear_profesor_nombre_duplicado(self, session: Session, profesor_factory):
        """Test: no se puede crear profesor con nombre duplicado."""
        # Crear profesor existente
        profesor_existente = profesor_factory(nombre_completo="Carlos Sánchez")
        session.add(profesor_existente)
        session.commit()

        use_case = CrearProfesorUseCase(session)

        dto = CrearProfesorDTO(
            nombre_completo="Carlos Sánchez",  # Nombre duplicado
            horas_contrato=25.0,
            turno="mañana",
        )

        with pytest.raises(ValidationError, match="Ya existe un profesor con el nombre"):
            use_case.execute(dto)

    def test_crear_profesor_horas_invalidas(self, session: Session):
        """Test: validar horas de contrato inválidas (debe fallar en DTO)."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            CrearProfesorDTO(
                nombre_completo="Test Profesor",
                horas_contrato=50.0,  # Más de 40 horas (inválido)
                turno="mañana",
            )

    def test_crear_profesor_error_bd(self, session: Session, mocker):
        """Test: rollback si hay error en la BD."""
        use_case = CrearProfesorUseCase(session)

        # Simular error en flush (el repositorio usa flush, no commit)
        mocker.patch.object(session, "flush", side_effect=Exception("DB Error"))

        dto = CrearProfesorDTO(
            nombre_completo="Test Error",
            horas_contrato=25.0,
            turno="mañana",
        )

        with pytest.raises(ValidationError, match="Error al crear profesor"):
            use_case.execute(dto)


# ================================
# Tests: ActualizarProfesorUseCase
# ================================


class TestActualizarProfesorUseCase:
    """Tests para el caso de uso de actualizar profesor."""

    def test_actualizar_profesor_nombre(self, session: Session, profesor_factory):
        """Test: actualizar nombre de profesor."""
        profesor = profesor_factory(nombre_completo="Ana Martínez")
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(nombre_completo="Ana María Martínez García")

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.nombre_completo == "Ana María Martínez García"
        assert resultado.id == profesor.id

    def test_actualizar_profesor_email_y_horas(self, session: Session, profesor_factory):
        """Test: actualizar email y horas de contrato."""
        profesor = profesor_factory(
            nombre_completo="Pedro González", horas_contrato=18.0, email_corporativo=None
        )
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(
            email_corporativo="pedro.gonzalez@colegio.edu", horas_contrato=25.0
        )

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.email_corporativo == "pedro.gonzalez@colegio.edu"
        assert resultado.horas_contrato == 25.0
        assert abs(resultado.porcentaje_jornada - 83.33) < 0.1  # (25/30)*100

    def test_actualizar_profesor_turno(self, session: Session, profesor_factory):
        """Test: actualizar turno de profesor."""
        profesor = profesor_factory(
            nombre_completo="Laura Fernández", turno="mañana", horas_manana=25.0, horas_tarde=0.0
        )
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(turno="mixto", horas_manana=15.0, horas_tarde=10.0)

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.turno == "mixto"
        assert resultado.horas_manana == 15.0
        assert resultado.horas_tarde == 10.0

    def test_actualizar_profesor_no_existente(self, session: Session):
        """Test: error al actualizar profesor que no existe."""
        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(nombre_completo="No Existe")

        with pytest.raises(NotFoundError):
            use_case.execute(9999, dto)

    def test_actualizar_profesor_nombre_duplicado(self, session: Session, profesor_factory):
        """Test: no se puede cambiar nombre a uno que ya existe."""
        profesor1 = profesor_factory(nombre_completo="Profesor Uno")
        profesor2 = profesor_factory(nombre_completo="Profesor Dos")
        session.add_all([profesor1, profesor2])
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(
            nombre_completo="Profesor Uno"  # Ya existe
        )

        with pytest.raises(BusinessLogicError, match="Ya existe otro profesor con el nombre"):
            use_case.execute(profesor2.id, dto)

    def test_actualizar_profesor_mismo_nombre(self, session: Session, profesor_factory):
        """Test: permitir mantener el mismo nombre al actualizar."""
        profesor = profesor_factory(nombre_completo="Mismo Nombre")
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(
            nombre_completo="Mismo Nombre",  # Mismo nombre
            horas_contrato=20.0,  # Cambiar otra cosa
        )

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.nombre_completo == "Mismo Nombre"
        assert resultado.horas_contrato == 20.0

    def test_actualizar_profesor_nombre_invalido(self, session: Session, profesor_factory):
        """Test: validar que Pydantic rechaza nombre muy corto."""
        profesor = profesor_factory(nombre_completo="Profesor Original")
        session.add(profesor)
        session.commit()

        # Pydantic valida en la creación del DTO
        with pytest.raises(Exception):  # ValidationError de Pydantic
            ActualizarProfesorDTO(nombre_completo="A")

    def test_actualizar_profesor_horas_invalidas(self, session: Session, profesor_factory):
        """Test: validar que Pydantic rechaza horas inválidas."""
        profesor = profesor_factory(nombre_completo="Profesor Test", horas_contrato=25.0)
        session.add(profesor)
        session.commit()

        # Pydantic valida en la creación del DTO
        with pytest.raises(Exception):  # ValidationError de Pydantic
            ActualizarProfesorDTO(horas_contrato=50.0)

    def test_actualizar_profesor_email_invalido(self, session: Session, profesor_factory):
        """Test: validar que Pydantic rechaza email inválido."""
        profesor = profesor_factory(nombre_completo="Profesor Email")
        session.add(profesor)
        session.commit()

        # Pydantic valida en la creación del DTO
        with pytest.raises(Exception):  # ValidationError de Pydantic
            ActualizarProfesorDTO(email_corporativo="email_sin_arroba")

    def test_actualizar_profesor_fechas_guardias(self, session: Session, profesor_factory):
        """Test: actualizar fechas de inicio y fin de guardias."""
        profesor = profesor_factory(nombre_completo="Profesor Fechas")
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(
            fecha_inicio_guardias=date(2024, 10, 1), fecha_fin_guardias=date(2025, 5, 31)
        )

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.fecha_inicio_guardias == date(2024, 10, 1)
        assert resultado.fecha_fin_guardias == date(2025, 5, 31)

    def test_actualizar_profesor_dias_semana_permitidos(self, session: Session, profesor_factory):
        """Test: actualizar días de la semana permitidos."""
        profesor = profesor_factory(nombre_completo="Profesor Dias")
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(
            dias_semana_permitidos=[0, 1, 2]  # Solo L, M, X
        )

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.dias_semana_permitidos == [0, 1, 2]

    def test_actualizar_profesor_recreos_permitidos(self, session: Session, profesor_factory):
        """Test: actualizar recreos permitidos."""
        profesor = profesor_factory(nombre_completo="Profesor Recreos")
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(
            recreos_permitidos=[1, 2, 3]  # Tres recreos
        )

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.recreos_permitidos == [1, 2, 3]

    def test_actualizar_profesor_tutor(self, session: Session, profesor_factory):
        """Test: actualizar campo tutor."""
        profesor = profesor_factory(nombre_completo="Profesor Tutor", tutor=False)
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        dto = ActualizarProfesorDTO(tutor=True)

        resultado = use_case.execute(profesor.id, dto)

        assert resultado.tutor is True

    def test_actualizar_profesor_error_commit(self, session: Session, profesor_factory, mocker):
        """Test: rollback si hay error en commit al actualizar."""
        profesor = profesor_factory(nombre_completo="Profesor Error")
        session.add(profesor)
        session.commit()

        use_case = ActualizarProfesorUseCase(session)

        # Simular error en commit
        mocker.patch.object(session, "commit", side_effect=Exception("DB Error"))

        dto = ActualizarProfesorDTO(nombre_completo="Nombre Actualizado")

        with pytest.raises(BusinessLogicError, match="Error al actualizar el profesor"):
            use_case.execute(profesor.id, dto)


# ================================
# Tests: EliminarProfesorUseCase
# ================================


class TestEliminarProfesorUseCase:
    """Tests para el caso de uso de eliminar profesor."""

    def test_eliminar_profesor_sin_guardias(self, session: Session, profesor_factory):
        """Test: eliminar profesor sin guardias asignadas."""
        profesor = profesor_factory(nombre_completo="A Eliminar")
        session.add(profesor)
        session.commit()
        profesor_id = profesor.id

        use_case = EliminarProfesorUseCase(session)
        use_case.execute(profesor_id)

        # Verificar que fue eliminado
        from infrastructure.database.models import Profesor

        profesor_bd = session.query(Profesor).filter_by(id=profesor_id).first()
        assert profesor_bd is None

    def test_eliminar_profesor_no_existente(self, session: Session):
        """Test: error al eliminar profesor que no existe."""
        use_case = EliminarProfesorUseCase(session)

        with pytest.raises(NotFoundError):
            use_case.execute(9999)

    def test_eliminar_profesor_con_guardias(
        self, session: Session, profesor_factory, zona_factory, guardia_factory
    ):
        """Test: no se puede eliminar profesor con guardias asignadas."""
        profesor = profesor_factory(nombre_completo="Con Guardias")
        zona = zona_factory(nombre_zona="Zona Test")
        session.add_all([profesor, zona])
        session.commit()

        # Asignar guardia
        guardia = guardia_factory(profesor_id=profesor.id, zona_id=zona.id)
        session.add(guardia)
        session.commit()

        use_case = EliminarProfesorUseCase(session)

        with pytest.raises(BusinessLogicError, match=r"guardia.*asignada"):
            use_case.execute(profesor.id)


# ===============================
# Tests: ObtenerProfesorUseCase
# ===============================


class TestObtenerProfesorUseCase:
    """Tests para el caso de uso de obtener profesor."""

    def test_obtener_profesor_por_id(self, session: Session, profesor_factory):
        """Test: obtener profesor existente por ID."""
        profesor = profesor_factory(
            nombre_completo="Profesor a Obtener",
            email_corporativo="obtener@test.com",
            horas_contrato=25.0,
            turno="mañana",
        )
        session.add(profesor)
        session.commit()

        use_case = ObtenerProfesorUseCase(session)
        resultado = use_case.execute(profesor.id)

        assert resultado.id == profesor.id
        assert resultado.nombre_completo == "Profesor a Obtener"
        assert resultado.email_corporativo == "obtener@test.com"
        assert resultado.horas_contrato == 25.0
        assert resultado.turno == "mañana"

    def test_obtener_profesor_no_existente(self, session: Session):
        """Test: error al obtener profesor que no existe."""
        use_case = ObtenerProfesorUseCase(session)

        with pytest.raises(NotFoundError):
            use_case.execute(9999)


# ================================
# Tests: ListarProfesoresUseCase
# ================================


class TestListarProfesoresUseCase:
    """Tests para el caso de uso de listar profesores."""

    def test_listar_profesores_vacio(self, session: Session):
        """Test: listar cuando no hay profesores devuelve lista vacía."""
        use_case = ListarProfesoresUseCase(session)
        resultado = use_case.execute()

        assert isinstance(resultado, list)
        assert len(resultado) == 0

    def test_listar_profesores_con_datos(self, session: Session, profesor_factory):
        """Test: listar devuelve todos los profesores."""
        prof1 = profesor_factory(nombre_completo="Profesor 1")
        prof2 = profesor_factory(nombre_completo="Profesor 2")
        prof3 = profesor_factory(nombre_completo="Profesor 3")
        session.add_all([prof1, prof2, prof3])
        session.commit()

        use_case = ListarProfesoresUseCase(session)
        resultado = use_case.execute()

        assert len(resultado) == 3
        assert all(isinstance(p, ProfesorDTO) for p in resultado)

    def test_listar_profesores_orden_alfabetico(self, session: Session, profesor_factory):
        """Test: los profesores se listan en orden alfabético."""
        prof_c = profesor_factory(nombre_completo="Carlos")
        prof_a = profesor_factory(nombre_completo="Ana")
        prof_b = profesor_factory(nombre_completo="Beatriz")
        session.add_all([prof_c, prof_a, prof_b])
        session.commit()

        use_case = ListarProfesoresUseCase(session)
        resultado = use_case.execute()

        assert len(resultado) == 3
        assert resultado[0].nombre_completo == "Ana"
        assert resultado[1].nombre_completo == "Beatriz"
        assert resultado[2].nombre_completo == "Carlos"


# =================================
# Tests: BuscarProfesoresUseCase
# =================================


class TestBuscarProfesoresUseCase:
    """Tests para el caso de uso de buscar profesores."""

    def test_buscar_profesor_por_nombre(self, session: Session, profesor_factory):
        """Test: buscar profesor por nombre (case-insensitive)."""
        prof1 = profesor_factory(nombre_completo="Juan García López")
        prof2 = profesor_factory(nombre_completo="María Pérez Sánchez")
        prof3 = profesor_factory(nombre_completo="Pedro García Martínez")
        session.add_all([prof1, prof2, prof3])
        session.commit()

        use_case = BuscarProfesoresUseCase(session)
        resultado = use_case.execute("garcía")  # Minúsculas

        assert len(resultado) == 2  # Juan García y Pedro García
        nombres = [p.nombre_completo for p in resultado]
        assert "Juan García López" in nombres
        assert "Pedro García Martínez" in nombres

    def test_buscar_profesor_por_email(self, session: Session, profesor_factory):
        """Test: buscar profesor por email (case-insensitive)."""
        prof1 = profesor_factory(
            nombre_completo="Ana Martínez", email_corporativo="ana@colegio.edu"
        )
        prof2 = profesor_factory(
            nombre_completo="Luis González", email_corporativo="luis@colegio.edu"
        )
        session.add_all([prof1, prof2])
        session.commit()

        use_case = BuscarProfesoresUseCase(session)
        resultado = use_case.execute("ANA")  # Mayúsculas

        assert len(resultado) == 1
        assert resultado[0].nombre_completo == "Ana Martínez"

    def test_buscar_profesor_termino_vacio(self, session: Session, profesor_factory):
        """Test: término vacío devuelve todos los profesores."""
        prof1 = profesor_factory(nombre_completo="Profesor 1")
        prof2 = profesor_factory(nombre_completo="Profesor 2")
        session.add_all([prof1, prof2])
        session.commit()

        use_case = BuscarProfesoresUseCase(session)
        resultado = use_case.execute("")  # Vacío

        assert len(resultado) == 2

    def test_buscar_profesor_sin_resultados(self, session: Session, profesor_factory):
        """Test: búsqueda sin resultados devuelve lista vacía."""
        prof1 = profesor_factory(nombre_completo="Juan Pérez")
        session.add(prof1)
        session.commit()

        use_case = BuscarProfesoresUseCase(session)
        resultado = use_case.execute("NOEXISTE")

        assert len(resultado) == 0


# ====================================
# Tests: Integración Profesor
# ====================================


class TestProfesorUseCasesIntegracion:
    """Tests de integración para flujos completos de Profesor."""

    def test_flujo_completo_crud_profesor(self, session: Session):
        """Test: flujo completo CRUD (Crear → Listar → Obtener → Actualizar → Eliminar)."""
        # 1. CREAR
        crear_use_case = CrearProfesorUseCase(session)
        dto_crear = CrearProfesorDTO(
            nombre_completo="Profesor Integración",
            email_corporativo="integracion@test.com",
            horas_contrato=25.0,
            turno="mañana",
        )
        profesor_creado = crear_use_case.execute(dto_crear)
        assert profesor_creado.id > 0
        profesor_id = profesor_creado.id

        # 2. LISTAR
        listar_use_case = ListarProfesoresUseCase(session)
        profesores = listar_use_case.execute()
        assert any(p.id == profesor_id for p in profesores)

        # 3. OBTENER
        obtener_use_case = ObtenerProfesorUseCase(session)
        profesor_obtenido = obtener_use_case.execute(profesor_id)
        assert profesor_obtenido.nombre_completo == "Profesor Integración"

        # 4. ACTUALIZAR
        actualizar_use_case = ActualizarProfesorUseCase(session)
        dto_actualizar = ActualizarProfesorDTO(nombre_completo="Profesor Integración Actualizado")
        profesor_actualizado = actualizar_use_case.execute(profesor_id, dto_actualizar)
        assert profesor_actualizado.nombre_completo == "Profesor Integración Actualizado"

        # 5. ELIMINAR
        eliminar_use_case = EliminarProfesorUseCase(session)
        eliminar_use_case.execute(profesor_id)

        # Verificar eliminación
        from infrastructure.database.models import Profesor

        profesor_bd = session.query(Profesor).filter_by(id=profesor_id).first()
        assert profesor_bd is None

    def test_buscar_despues_de_crear(self, session: Session):
        """Test: buscar encuentra profesores recién creados."""
        crear_use_case = CrearProfesorUseCase(session)

        # Crear varios profesores
        crear_use_case.execute(
            CrearProfesorDTO(nombre_completo="Alberto Ramírez", horas_contrato=25.0, turno="mañana")
        )
        crear_use_case.execute(
            CrearProfesorDTO(nombre_completo="Alberto Sánchez", horas_contrato=18.0, turno="tarde")
        )
        crear_use_case.execute(
            CrearProfesorDTO(nombre_completo="María Torres", horas_contrato=25.0, turno="mañana")
        )

        # Buscar por "Alberto"
        buscar_use_case = BuscarProfesoresUseCase(session)
        resultado = buscar_use_case.execute("Alberto")

        assert len(resultado) == 2
        assert all("Alberto" in p.nombre_completo for p in resultado)

    def test_listar_despues_de_crear_multiples(self, session: Session):
        """Test: listar muestra todos los profesores creados en orden."""
        crear_use_case = CrearProfesorUseCase(session)

        # Crear 5 profesores
        nombres = ["Zoe", "Ana", "María", "Carlos", "Beatriz"]
        for nombre in nombres:
            crear_use_case.execute(
                CrearProfesorDTO(nombre_completo=nombre, horas_contrato=25.0, turno="mañana")
            )

        # Listar
        listar_use_case = ListarProfesoresUseCase(session)
        resultado = listar_use_case.execute()

        assert len(resultado) == 5
        # Verificar orden alfabético
        nombres_resultado = [p.nombre_completo for p in resultado]
        assert nombres_resultado == ["Ana", "Beatriz", "Carlos", "María", "Zoe"]
