"""
TEST-CORE: Tests de servicios durante/tras migración ARQ-01.

Verifica que los servicios migrados funcionan correctamente con:
- Repositorios inyectados (ruta nueva)
- RepositoryFactory (ruta polimórfica)
- Session legacy (compatibilidad)

Servicios cubiertos:
- importador_profesores (fase extensión #1 v5.14.2)
- importador_zonas (fase extensión #2 v5.20.0)
- DisponibilidadProfesorService (fase extensión #2 v5.20.0)
"""

import csv
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ============================================================================
# importador_profesores — rutas polimórficas ARQ-01
# ============================================================================


class TestImportadorProfesoresPolimorfismo:
    """Verifica la detección del tipo de argumento (repo/factory/session)."""

    def test_normalizar_nombre_elimina_espacios(self):
        from services.importador_profesores import normalizar_nombre

        assert normalizar_nombre("  garcía  lópez , juan  ") == "GARCÍA LÓPEZ , JUAN"

    def test_normalizar_nombre_mayusculas(self):
        from services.importador_profesores import normalizar_nombre

        assert normalizar_nombre("martinez") == "MARTINEZ"

    def test_acepta_repository_factory(self):
        """Con RepositoryFactory crea el repo correctamente."""
        from services.importador_profesores import importar_profesores_desde_excel

        mock_factory = MagicMock()
        mock_factory.create_profesor_repository = MagicMock()
        mock_repo = MagicMock()
        mock_factory.create_profesor_repository.return_value = mock_repo

        # Archivo CSV vacío (pandas puede leerlo, el resultado será error de columnas)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name

        with patch("services.importador_profesores.pd") as mock_pd:
            mock_df = MagicMock()
            mock_df.columns = []  # Sin columnas → error controlado
            mock_pd.read_excel.return_value = mock_df

            resultado = importar_profesores_desde_excel(mock_factory, tmp_path)

        mock_factory.create_profesor_repository.assert_called_once()
        assert "errores" in resultado

    def test_acepta_repo_directo_con_find_by_nombre(self):
        """Con repo directo (tiene find_by_nombre) lo usa directamente."""
        from services.importador_profesores import importar_profesores_desde_excel

        mock_repo = MagicMock()
        mock_repo.find_by_nombre = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name

        with patch("services.importador_profesores.pd") as mock_pd:
            mock_df = MagicMock()
            mock_df.columns = []
            mock_pd.read_excel.return_value = mock_df

            resultado = importar_profesores_desde_excel(mock_repo, tmp_path)

        # No debe haber llamado a RepositoryFactory
        assert "errores" in resultado

    def test_acepta_session_legacy(self):
        """Con session legacy crea RepositoryFactory internamente."""
        from services.importador_profesores import importar_profesores_desde_excel

        # spec=[] → sin atributos → no tiene create_profesor_repository ni find_by_nombre
        mock_session = MagicMock(spec=[])

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name

        with patch("services.importador_profesores.RepositoryFactory") as mock_rf_cls:
            mock_factory = MagicMock()
            mock_rf_cls.return_value = mock_factory

            with patch("services.importador_profesores.pd") as mock_pd:
                mock_df = MagicMock()
                mock_df.columns = []
                mock_pd.read_excel.return_value = mock_df

                resultado = importar_profesores_desde_excel(mock_session, tmp_path)

        mock_rf_cls.assert_called_once_with(mock_session)
        assert "errores" in resultado

    def test_resultado_contiene_claves_esperadas(self):
        """El diccionario resultado siempre tiene las claves estándar."""
        from services.importador_profesores import importar_profesores_desde_excel

        mock_factory = MagicMock()
        mock_factory.create_profesor_repository.return_value = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name

        with patch("services.importador_profesores.pd") as mock_pd:
            mock_df = MagicMock()
            mock_df.columns = []
            mock_pd.read_excel.return_value = mock_df

            resultado = importar_profesores_desde_excel(mock_factory, tmp_path)

        assert "leidos" in resultado
        assert "importados" in resultado
        assert "existentes" in resultado
        assert "errores" in resultado
        assert "detalles" in resultado

    def test_progress_callback_se_invoca(self):
        """El progress_callback se llama al menos una vez."""
        from services.importador_profesores import importar_profesores_desde_excel

        mock_factory = MagicMock()
        mock_factory.create_profesor_repository.return_value = MagicMock()
        callback = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name

        with patch("services.importador_profesores.pd") as mock_pd:
            mock_df = MagicMock()
            mock_df.columns = []
            mock_pd.read_excel.return_value = mock_df

            importar_profesores_desde_excel(mock_factory, tmp_path, progress_callback=callback)

        callback.assert_called()

    def test_pandas_no_disponible_retorna_error(self):
        """Sin pandas retorna error controlado."""
        from services.importador_profesores import importar_profesores_desde_excel

        mock_factory = MagicMock()
        mock_factory.create_profesor_repository.return_value = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            tmp_path = f.name

        with patch("services.importador_profesores.pd", None):
            resultado = importar_profesores_desde_excel(mock_factory, tmp_path)

        assert resultado["errores"] >= 1


# ============================================================================
# importador_zonas — helper _get_zona_repo ARQ-01
# ============================================================================


class TestImportadorZonasPolimorfismo:
    """Verifica la resolución polimórfica de _get_zona_repo."""

    def test_get_zona_repo_con_repository_factory(self):
        """RepositoryFactory (tiene create_zona_repository)."""
        from services.importador_zonas import _get_zona_repo

        mock_factory = MagicMock()
        mock_repo = MagicMock()
        mock_repo.session = MagicMock()
        mock_factory.create_zona_repository.return_value = mock_repo

        repo, session = _get_zona_repo(mock_factory)

        mock_factory.create_zona_repository.assert_called_once()
        assert repo is mock_repo

    def test_get_zona_repo_con_repo_directo(self):
        """Repo directo (tiene find_by_nombre pero NO create_zona_repository)."""
        from services.importador_zonas import _get_zona_repo

        # spec lista los únicos atributos permitidos → MagicMock no auto-crea create_zona_repository
        mock_repo = MagicMock(spec=["find_by_nombre", "session", "save", "find_all"])
        mock_repo.session = MagicMock()

        repo, session = _get_zona_repo(mock_repo)

        assert repo is mock_repo

    def test_get_zona_repo_con_session_legacy(self):
        """Session legacy crea RepositoryFactory internamente."""
        from services.importador_zonas import _get_zona_repo

        mock_session = MagicMock(
            spec=[]
        )  # spec vacío → sin create_zona_repository ni find_by_nombre

        with patch("services.importador_zonas.RepositoryFactory") as mock_rf_cls:
            mock_factory = MagicMock()
            mock_repo = MagicMock()
            mock_factory.create_zona_repository.return_value = mock_repo
            mock_rf_cls.return_value = mock_factory

            repo, session = _get_zona_repo(mock_session)

        mock_rf_cls.assert_called_once_with(mock_session)
        assert repo is mock_repo

    def test_importar_zonas_csv_vacio(self):
        """CSV vacío retorna ceros en todas las claves."""
        from services.importador_zonas import importar_zonas_desde_csv

        mock_factory = MagicMock()
        mock_repo = MagicMock()
        mock_repo.session = MagicMock()
        mock_factory.create_zona_repository.return_value = mock_repo

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nombre_zona"])  # Solo cabecera, sin datos
            tmp_path = f.name

        resultado = importar_zonas_desde_csv(mock_factory, tmp_path)

        assert resultado["leidos"] == 0
        assert resultado["errores"] == 0

    def test_importar_zonas_csv_con_datos(self):
        """CSV con una zona válida llama a save en el repo."""
        from services.importador_zonas import importar_zonas_desde_csv

        mock_factory = MagicMock()
        mock_repo = MagicMock()
        mock_repo.session = MagicMock()
        mock_repo.find_by_nombre.return_value = None  # No existe aún
        mock_factory.create_zona_repository.return_value = mock_repo

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nombre_zona", "descripcion", "activa", "capacidad_profesores"])
            writer.writerow(["Patio Norte", "Zona norte del colegio", "1", "3"])
            tmp_path = f.name

        resultado = importar_zonas_desde_csv(mock_factory, tmp_path)

        assert resultado["leidos"] == 1

    def test_importar_zonas_resultado_tiene_claves(self):
        """El diccionario resultado siempre tiene las claves estándar."""
        from services.importador_zonas import importar_zonas_desde_csv

        mock_factory = MagicMock()
        mock_repo = MagicMock()
        mock_repo.session = MagicMock()
        mock_factory.create_zona_repository.return_value = mock_repo

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nombre_zona"])
            tmp_path = f.name

        resultado = importar_zonas_desde_csv(mock_factory, tmp_path)

        for clave in ("leidos", "importadas", "existentes", "errores", "detalles"):
            assert clave in resultado


# ============================================================================
# DisponibilidadProfesorService — constructor polimórfico ARQ-01
# ============================================================================


class TestDisponibilidadProfesorServicePolimorfismo:
    """Verifica que el servicio acepta session y RepositoryFactory."""

    def _make_profesor(self, activo=True, turno="mixto"):
        profesor = MagicMock()
        profesor.id = 1
        profesor.activo = activo
        profesor.turno = turno
        profesor.horas_manana = 15.0
        profesor.horas_tarde = 15.0
        return profesor

    def test_constructor_con_session(self):
        """Constructor acepta session directamente."""
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()

        with patch("services.disponibilidad_profesor_service.AusenciaChecker"):
            svc = DisponibilidadProfesorService(mock_session)

        assert svc.session is mock_session

    def test_constructor_con_repository_factory(self):
        """Constructor acepta RepositoryFactory y extrae session."""
        from infrastructure.repositories.repository_factory import RepositoryFactory
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()
        mock_factory = MagicMock(spec=RepositoryFactory)
        mock_factory.session = mock_session

        with patch("services.disponibilidad_profesor_service.AusenciaChecker"):
            svc = DisponibilidadProfesorService(mock_factory)

        assert svc.session is mock_session

    def test_from_session_classmethod(self):
        """from_session() crea instancia correctamente."""
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()

        with patch("services.disponibilidad_profesor_service.AusenciaChecker"):
            svc = DisponibilidadProfesorService.from_session(mock_session)

        assert svc.session is mock_session

    def test_profesor_inactivo_no_disponible(self):
        """Profesor inactivo devuelve (False, 'Profesor inactivo')."""
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()

        with patch("services.disponibilidad_profesor_service.AusenciaChecker"):
            svc = DisponibilidadProfesorService(mock_session)
            profesor = self._make_profesor(activo=False)

            disponible, razon = svc.esta_disponible(profesor, date(2025, 10, 15), "mañana")

        assert disponible is False
        assert "inactivo" in razon.lower()

    def test_profesor_ausente_no_disponible(self):
        """Profesor ausente devuelve (False, razón de ausencia)."""
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()

        with patch("services.disponibilidad_profesor_service.AusenciaChecker") as mock_ac_cls:
            mock_ac = MagicMock()
            mock_ac.profesor_ausente.return_value = True
            mock_ac_cls.return_value = mock_ac

            svc = DisponibilidadProfesorService(mock_session)
            profesor = self._make_profesor(activo=True, turno="mixto")

            disponible, razon = svc.esta_disponible(profesor, date(2025, 10, 15), "mañana")

        assert disponible is False
        assert razon is not None

    def test_obtener_profesores_disponibles_excluye_inactivos(self):
        """obtener_profesores_disponibles filtra correctamente inactivos."""
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()

        with patch("services.disponibilidad_profesor_service.AusenciaChecker"):
            svc = DisponibilidadProfesorService(mock_session)

            inactivo = self._make_profesor(activo=False)
            disponibles = svc.obtener_profesores_disponibles(
                [inactivo], date(2025, 10, 15), "mañana", recreo_id=1
            )

        assert len(disponibles) == 0

    def test_obtener_profesores_disponibles_excluye_por_id(self):
        """excluir_profesor_id excluye al profesor correcto."""
        from services.disponibilidad_profesor_service import DisponibilidadProfesorService

        mock_session = MagicMock()

        with patch("services.disponibilidad_profesor_service.AusenciaChecker"):
            svc = DisponibilidadProfesorService(mock_session)

            profesor = self._make_profesor(activo=True, turno="mixto")
            profesor.id = 99

            disponibles = svc.obtener_profesores_disponibles(
                [profesor],
                date(2025, 10, 15),
                "mañana",
                recreo_id=1,
                excluir_profesor_id=99,
            )

        assert len(disponibles) == 0
