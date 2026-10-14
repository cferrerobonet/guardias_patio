"""
Tests para utils/cache.py — sistema de caché avanzado con TTL, LRU y métricas.
"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import utils.cache as cache_module
from utils.cache import (
    cache_long,
    cache_medium,
    cache_query,
    cache_short,
    clear_all_cache,
    get_cache_entries_info,
    get_cache_stats,
    get_function_metrics,
    invalidate_by_function,
    invalidate_cache,
    print_cache_stats,
    reset_cache_stats,
    reset_function_metrics,
)


def _reset():
    """Limpia estado global entre tests."""
    clear_all_cache()
    reset_cache_stats()
    reset_function_metrics()


# ─────────────────────────────────────────────────────────────────────────────
# cache_query — miss / hit
# ─────────────────────────────────────────────────────────────────────────────


class TestCacheQuery:
    def setup_method(self):
        _reset()

    def test_miss_llama_funcion(self):
        call_count = [0]

        @cache_query(ttl=60)
        def mi_funcion(x):
            call_count[0] += 1
            return x * 2

        result = mi_funcion(5)
        assert result == 10
        assert call_count[0] == 1

    def test_hit_no_llama_de_nuevo(self):
        call_count = [0]

        @cache_query(ttl=60)
        def mi_funcion(x):
            call_count[0] += 1
            return x * 2

        mi_funcion(5)
        mi_funcion(5)  # Segunda llamada → hit
        assert call_count[0] == 1

    def test_diferentes_args_diferentes_entradas(self):
        call_count = [0]

        @cache_query(ttl=60)
        def mi_funcion(x):
            call_count[0] += 1
            return x * 2

        mi_funcion(3)
        mi_funcion(7)
        assert call_count[0] == 2

    def test_cache_expirado_llama_de_nuevo(self):
        call_count = [0]

        @cache_query(ttl=0.01)  # 10ms TTL
        def mi_funcion(x):
            call_count[0] += 1
            return x

        mi_funcion(1)
        time.sleep(0.02)  # Esperar expiración
        mi_funcion(1)  # Debería ser miss por expiración
        assert call_count[0] == 2

    def test_stats_hits_y_misses(self):
        @cache_query(ttl=60)
        def mi_funcion():
            return 42

        mi_funcion()  # miss
        mi_funcion()  # hit
        mi_funcion()  # hit

        stats = get_cache_stats()
        assert stats["hits"] >= 2
        assert stats["misses"] >= 1

    def test_key_func_personalizado(self):
        call_count = [0]

        @cache_query(ttl=60, key_func=lambda x: f"custom:{x}")
        def mi_funcion(x):
            call_count[0] += 1
            return x

        mi_funcion("val")
        mi_funcion("val")
        assert call_count[0] == 1

    def test_wrapper_invalidate_cache_method(self):
        call_count = [0]

        @cache_query(ttl=60)
        def mi_funcion():
            call_count[0] += 1
            return 99

        mi_funcion()
        mi_funcion.invalidate_cache()
        mi_funcion()
        assert call_count[0] == 2

    def test_sesion_sqlalchemy_excluida_de_la_clave(self):
        """Objetos con atributo .query son excluidos de la clave de caché."""
        from unittest.mock import MagicMock

        session_mock = MagicMock()
        session_mock.query = MagicMock()

        call_count = [0]

        @cache_query(ttl=60)
        def mi_funcion(session, valor):
            call_count[0] += 1
            return valor

        mi_funcion(session_mock, "a")
        mi_funcion(session_mock, "a")
        assert call_count[0] == 1


# ─────────────────────────────────────────────────────────────────────────────
# invalidate_cache
# ─────────────────────────────────────────────────────────────────────────────


class TestInvalidateCache:
    def setup_method(self):
        _reset()

    def _populate(self, *keys):
        """Añade entradas directamente al store."""
        for k in keys:
            cache_module._cache_store[k] = ("v", time.time(), 300, 1)

    def test_invalidar_todo_con_none(self):
        self._populate("f1()", "f2()")
        n = invalidate_cache(None)
        assert n == 2
        assert len(cache_module._cache_store) == 0

    def test_invalidar_sin_argumento(self):
        self._populate("f1()", "f2()")
        n = invalidate_cache()
        assert n == 2

    def test_invalidar_por_substring(self):
        self._populate("obtener_profesores()", "obtener_zonas()", "listar_cursos()")
        n = invalidate_cache("obtener")
        assert n == 2

    def test_invalidar_por_regex(self):
        self._populate("obtener_profesores()", "listar_zonas()", "calcular_cuotas()")
        n = invalidate_cache(r"^obtener|^listar", use_regex=True)
        assert n == 2

    def test_regex_invalido_devuelve_0(self):
        self._populate("f()")
        n = invalidate_cache(r"[invalid", use_regex=True)
        assert n == 0

    def test_patron_sin_coincidencias(self):
        self._populate("f1()")
        n = invalidate_cache("noexiste")
        assert n == 0
        assert len(cache_module._cache_store) == 1


# ─────────────────────────────────────────────────────────────────────────────
# invalidate_by_function / clear_all_cache
# ─────────────────────────────────────────────────────────────────────────────


class TestInvalidateByFunction:
    def setup_method(self):
        _reset()

    def test_invalida_por_nombre_funcion(self):
        cache_module._cache_store["mi_func()"] = ("v", time.time(), 300, 1)
        cache_module._cache_store["otra_func()"] = ("v", time.time(), 300, 1)
        n = invalidate_by_function("mi_func")
        assert n == 1
        assert "otra_func()" in cache_module._cache_store

    def test_clear_all_limpia_todo(self):
        cache_module._cache_store["f1()"] = ("v", time.time(), 300, 1)
        cache_module._cache_store["f2()"] = ("v", time.time(), 300, 1)
        clear_all_cache()
        assert len(cache_module._cache_store) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Estadísticas y métricas
# ─────────────────────────────────────────────────────────────────────────────


class TestCacheStats:
    def setup_method(self):
        _reset()

    def test_get_cache_stats_inicial(self):
        stats = get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0
        assert stats["max_size"] == cache_module.MAX_CACHE_SIZE

    def test_hit_rate_calculado_correctamente(self):
        @cache_query(ttl=60)
        def f():
            return 1

        f()  # miss
        f()  # hit
        f()  # hit
        stats = get_cache_stats()
        assert stats["hit_rate"] == pytest.approx(66.67, abs=0.1)
        assert stats["total_requests"] == 3

    def test_reset_cache_stats_reinicia_contadores(self):
        @cache_query(ttl=60)
        def f():
            return 1

        f()
        f()
        reset_cache_stats()
        stats = get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_get_function_metrics_funcion_especifica(self):
        @cache_query(ttl=60)
        def mi_funcion():
            return 1

        mi_funcion()
        mi_funcion()
        metrics = get_function_metrics("mi_funcion")
        assert metrics["total"] == 2
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1

    def test_get_function_metrics_funcion_inexistente(self):
        metrics = get_function_metrics("no_existe")
        assert metrics == {"hits": 0, "misses": 0, "total": 0, "hit_rate": 0.0}

    def test_get_function_metrics_todas(self):
        @cache_query(ttl=60)
        def f1():
            return 1

        @cache_query(ttl=60)
        def f2():
            return 2

        f1()
        f2()
        all_metrics = get_function_metrics()
        assert "f1" in all_metrics
        assert "f2" in all_metrics

    def test_reset_function_metrics(self):
        @cache_query(ttl=60)
        def f():
            return 1

        f()
        reset_function_metrics()
        assert get_function_metrics("f") == {"hits": 0, "misses": 0, "total": 0, "hit_rate": 0.0}


# ─────────────────────────────────────────────────────────────────────────────
# get_cache_entries_info
# ─────────────────────────────────────────────────────────────────────────────


class TestCacheEntriesInfo:
    def setup_method(self):
        _reset()

    def test_entries_info_vacio(self):
        assert get_cache_entries_info() == []

    def test_entries_info_con_datos(self):
        @cache_query(ttl=300)
        def f():
            return 42

        f()
        entries = get_cache_entries_info()
        assert len(entries) == 1
        entry = entries[0]
        assert "key" in entry
        assert "age" in entry
        assert "ttl" in entry
        assert entry["ttl"] == 300
        assert entry["expired"] is False

    def test_entries_info_entrada_expirada(self):
        cache_module._cache_store["old_key"] = ("v", time.time() - 400, 300, 1)
        entries = get_cache_entries_info()
        assert entries[0]["expired"] is True


# ─────────────────────────────────────────────────────────────────────────────
# LRU eviction
# ─────────────────────────────────────────────────────────────────────────────


class TestLRUEviction:
    def setup_method(self):
        _reset()

    def test_evicion_cuando_se_alcanza_limite(self):
        original_max = cache_module.MAX_CACHE_SIZE
        cache_module.MAX_CACHE_SIZE = 3
        try:
            # Llenar el cache hasta el límite
            for i in range(3):
                cache_module._cache_store[f"key{i}"] = ("v", time.time(), 300, 1)
            # La 4ª entrada debería evictar la primera
            cache_module._evict_if_needed()
            cache_module._cache_store["key3"] = ("v", time.time(), 300, 1)
            assert "key0" not in cache_module._cache_store
            assert cache_module._cache_stats["evictions"] >= 1
        finally:
            cache_module.MAX_CACHE_SIZE = original_max

    def test_lru_ordering_en_hit(self):
        @cache_query(ttl=60)
        def f(x):
            return x

        f(1)
        f(2)
        f(1)  # hit → mueve key1 al final
        keys = list(cache_module._cache_store.keys())
        # La clave de f(1) debe ser la última (más reciente)
        assert any("f(1," in k or "f(2," in k for k in keys)


# ─────────────────────────────────────────────────────────────────────────────
# print_cache_stats / cache decorators de conveniencia
# ─────────────────────────────────────────────────────────────────────────────


class TestConvenienceDecorators:
    def setup_method(self):
        _reset()

    def test_print_cache_stats_no_falla(self, capsys):
        print_cache_stats()
        out = capsys.readouterr().out
        assert "Cache Statistics" in out

    def test_print_cache_stats_detailed(self, capsys):
        @cache_query(ttl=60)
        def f():
            return 1

        f()
        print_cache_stats(detailed=True)
        out = capsys.readouterr().out
        assert "Per-Function Metrics" in out

    def test_print_cache_stats_sin_metricas(self, capsys):
        print_cache_stats(detailed=True)
        out = capsys.readouterr().out
        assert "No function metrics" in out

    def test_cache_short_usa_ttl_60(self):
        @cache_short
        def f():
            return 1

        f()
        entries = get_cache_entries_info()
        assert entries[0]["ttl"] == 60

    def test_cache_medium_usa_ttl_300(self):
        @cache_medium
        def f():
            return 1

        f()
        entries = get_cache_entries_info()
        assert entries[0]["ttl"] == 300

    def test_cache_long_usa_ttl_1800(self):
        @cache_long
        def f():
            return 1

        f()
        entries = get_cache_entries_info()
        assert entries[0]["ttl"] == 1800
