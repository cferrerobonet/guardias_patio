"""
Tests basados en propiedades (Hypothesis).

Cubre invariantes del dominio que los tests enumerados no pueden explorar:
- Política de contraseñas: cualquier combinación válida pasa, cualquier violación falla.
- JWT: round-trip encode→decode preserva el username.
- LocalSyncBackend: path traversal siempre rechazado, rutas válidas siempre permitidas.
- ZonaDTO: validación de nombres.
"""

import string
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sync.sync_manager import LocalSyncBackend, UserAuth

# ============================================================================
# ESTRATEGIAS REUTILIZABLES
# ============================================================================

# Contraseñas que cumplen TODOS los requisitos (mínimo 8 chars)
_VALID_PASSWORD = st.builds(
    lambda base, upper, digit, special: base + upper + digit + special,
    base=st.text(alphabet=string.ascii_lowercase, min_size=5, max_size=12),
    upper=st.text(alphabet=string.ascii_uppercase, min_size=1, max_size=3),
    digit=st.text(alphabet=string.digits, min_size=1, max_size=3),
    special=st.sampled_from(list("!@#$%^&*()_+-=[]{}|;':,./<>?")),
)

# Nombres de fichero seguros (sin '..' ni separadores de ruta)
_SAFE_FILENAME = st.text(
    alphabet=string.ascii_lowercase + string.digits + "_-",
    min_size=1,
    max_size=40,
)


def _fresh_backend() -> LocalSyncBackend:
    """Crea un backend con directorio temporal nuevo."""
    tmp = tempfile.mkdtemp()
    return LocalSyncBackend(Path(tmp) / "base")


# ============================================================================
# TESTS: Política de contraseñas
# ============================================================================


class TestPasswordPolicyHypothesis:
    @given(_VALID_PASSWORD)
    def test_contrasena_valida_siempre_pasa(self, password):
        ok, msg = UserAuth.validate_password_policy(password)
        assert ok is True, f"Contraseña válida rechazada: {password!r} — {msg}"

    @given(st.text(alphabet=string.ascii_lowercase + string.digits, max_size=7))
    def test_contrasena_sin_mayuscula_falla(self, password):
        ok, _ = UserAuth.validate_password_policy(password)
        assert ok is False

    @given(st.text(alphabet=string.ascii_letters, min_size=8, max_size=20))
    def test_contrasena_sin_digito_ni_especial_falla(self, password):
        assume(any(c.isupper() for c in password))
        ok, _ = UserAuth.validate_password_policy(password)
        assert ok is False

    @given(st.text(min_size=0, max_size=7))
    def test_contrasena_corta_siempre_falla(self, password):
        ok, msg = UserAuth.validate_password_policy(password)
        assert ok is False
        assert msg != ""

    @given(
        st.text(
            alphabet=string.ascii_letters + string.digits, min_size=8, max_size=20
        ).filter(lambda p: any(c.isupper() for c in p) and any(c.isdigit() for c in p))
    )
    def test_contrasena_sin_especial_falla(self, password):
        assume(not any(c in "!@#$%^&*()_+-=[]{}|;':,./<>?" for c in password))
        ok, _ = UserAuth.validate_password_policy(password)
        assert ok is False


# ============================================================================
# TESTS: JWT round-trip
# ============================================================================


class TestJWTRoundTrip:
    @given(
        st.text(
            alphabet=string.ascii_letters + string.digits + "_-.",
            min_size=1,
            max_size=50,
        )
    )
    def test_username_sobrevive_encode_decode(self, username):
        from api.auth import _create_access_token, get_current_user

        token = _create_access_token(username)
        decoded = get_current_user(token)
        assert decoded == username

    @given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=50))
    @settings(max_examples=30)
    def test_cualquier_username_genera_token_con_tres_partes(self, username):
        from api.auth import _create_access_token

        token = _create_access_token(username)
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT: header.payload.signature


# ============================================================================
# TESTS: LocalSyncBackend — path traversal (Hypothesis)
# ============================================================================


class TestPathTraversalHypothesis:
    @given(
        st.integers(min_value=1, max_value=5).flatmap(
            lambda n: st.just("../" * n + "evil.txt")
        )
    )
    @settings(max_examples=20)
    def test_path_con_traversal_inicial_rechazado(self, dangerous_path):
        backend = _fresh_backend()
        with pytest.raises(ValueError):
            backend._safe_path(dangerous_path)

    @given(_SAFE_FILENAME)
    def test_filename_seguro_no_lanza_excepcion(self, safe_name):
        backend = _fresh_backend()
        result = backend._safe_path(safe_name)
        assert str(result.resolve()).startswith(str(backend.base_path.resolve()))

    @given(
        st.lists(_SAFE_FILENAME, min_size=1, max_size=4).map(lambda parts: "/".join(parts))
    )
    def test_ruta_con_subdirectorios_seguros_permitida(self, safe_path):
        backend = _fresh_backend()
        result = backend._safe_path(safe_path)
        assert str(result.resolve()).startswith(str(backend.base_path.resolve()))

    @pytest.mark.parametrize(
        "dangerous",
        [
            "../etc/passwd",
            "../../root/.ssh/id_rsa",
            "subdir/../../../outside",
            "../outside",
        ],
    )
    def test_patrones_clasicos_de_traversal_rechazados(self, dangerous):
        backend = _fresh_backend()
        with pytest.raises(ValueError):
            backend._safe_path(dangerous)


# ============================================================================
# TESTS: ZonaDTO — validación de nombres
# ============================================================================


class TestZonaDTOHypothesis:
    @given(
        st.text(
            alphabet=string.ascii_letters + string.digits + " ñÑáéíóúÁÉÍÓÚ",
            min_size=2,
            max_size=100,
        ).filter(lambda s: len(s.strip()) >= 2)
    )
    def test_nombre_valido_no_falla_validacion(self, nombre):
        from application.dtos.zona_dto import CrearZonaDTO

        dto = CrearZonaDTO(nombre_zona=nombre)
        assert len(dto.nombre_zona) >= 2

    @given(st.just("") | st.just(" ") | st.just("  "))
    def test_nombre_vacio_lanza_error(self, nombre_vacio):
        from pydantic import ValidationError
        from application.dtos.zona_dto import CrearZonaDTO

        with pytest.raises(ValidationError):
            CrearZonaDTO(nombre_zona=nombre_vacio)

    @given(st.text(min_size=1, max_size=1))
    def test_nombre_un_caracter_lanza_error(self, nombre_corto):
        from pydantic import ValidationError
        from application.dtos.zona_dto import CrearZonaDTO

        with pytest.raises(ValidationError):
            CrearZonaDTO(nombre_zona=nombre_corto)
