"""
Tests para las optimizaciones de rendimiento del asignador.

Verifica que IndiceSlots, FiltroProfesores y otras estructuras
funcionan correctamente y mantienen la equidad del algoritmo.
"""

from datetime import date

from infrastructure.database.models import Guardia, Profesor
from services.optimizaciones_asignador import (
    CacheElegibilidad,
    FiltroProfesores,
    IndiceSlots,
    SlotKey,
    agrupar_slots_por_fecha,
    estadisticas_rendimiento,
    ordenar_profesores_equitativamente,
    validar_indices,
)


class TestIndiceSlots:
    """Tests para el índice de slots ocupados."""

    def test_crear_indice_vacio(self):
        """Verificar que se puede crear un índice vacío."""
        indice = IndiceSlots()
        assert indice.total_ocupados() == 0

    def test_marcar_ocupado(self):
        """Verificar que se puede marcar un slot como ocupado."""
        indice = IndiceSlots()
        fecha = date(2025, 10, 1)

        indice.marcar_ocupado(fecha, "mañana", 1, 1)
        assert indice.esta_ocupado(fecha, "mañana", 1, 1)
        assert indice.total_ocupados() == 1

    def test_slot_no_ocupado(self):
        """Verificar que un slot no marcado no está ocupado."""
        indice = IndiceSlots()
        fecha = date(2025, 10, 1)

        assert not indice.esta_ocupado(fecha, "mañana", 1, 1)

    def test_desmarcar_slot(self):
        """Verificar que se puede desmarcar un slot."""
        indice = IndiceSlots()
        fecha = date(2025, 10, 1)

        indice.marcar_ocupado(fecha, "mañana", 1, 1)
        assert indice.esta_ocupado(fecha, "mañana", 1, 1)

        indice.desmarcar(fecha, "mañana", 1, 1)
        assert not indice.esta_ocupado(fecha, "mañana", 1, 1)
        assert indice.total_ocupados() == 0

    def test_slots_diferentes_son_independientes(self):
        """Verificar que diferentes slots son independientes."""
        indice = IndiceSlots()
        fecha = date(2025, 10, 1)

        indice.marcar_ocupado(fecha, "mañana", 1, 1)

        # Fecha diferente
        assert not indice.esta_ocupado(date(2025, 10, 2), "mañana", 1, 1)
        # Turno diferente
        assert not indice.esta_ocupado(fecha, "tarde", 1, 1)
        # Recreo diferente
        assert not indice.esta_ocupado(fecha, "mañana", 2, 1)
        # Zona diferente
        assert not indice.esta_ocupado(fecha, "mañana", 1, 2)

    def test_desde_calendario_vacio(self):
        """Verificar creación desde calendario vacío."""
        calendario = []
        indice = IndiceSlots.desde_calendario(calendario)
        assert indice.total_ocupados() == 0

    def test_desde_calendario_con_guardias(self):
        """Verificar creación desde calendario con guardias."""
        fecha = date(2025, 10, 1)

        # Crear guardias mock
        guardia1 = Guardia(fecha=fecha, turno="mañana", recreo=1, zona_id=1, profesor_id=1)
        guardia2 = Guardia(fecha=fecha, turno="mañana", recreo=2, zona_id=1, profesor_id=2)

        calendario = [guardia1, guardia2]
        indice = IndiceSlots.desde_calendario(calendario)

        assert indice.total_ocupados() == 2
        assert indice.esta_ocupado(fecha, "mañana", 1, 1)
        assert indice.esta_ocupado(fecha, "mañana", 2, 1)


class TestSlotKey:
    """Tests para la clave de slot."""

    def test_crear_slot_key(self):
        """Verificar que se puede crear un SlotKey."""
        fecha = date(2025, 10, 1)
        key = SlotKey(fecha, "mañana", 1, 1)

        assert key.fecha == fecha
        assert key.turno == "mañana"
        assert key.recreo == 1
        assert key.zona_id == 1

    def test_slot_keys_iguales(self):
        """Verificar que SlotKeys iguales son iguales."""
        fecha = date(2025, 10, 1)
        key1 = SlotKey(fecha, "mañana", 1, 1)
        key2 = SlotKey(fecha, "mañana", 1, 1)

        assert key1 == key2
        assert hash(key1) == hash(key2)

    def test_slot_keys_diferentes(self):
        """Verificar que SlotKeys diferentes no son iguales."""
        fecha = date(2025, 10, 1)
        key1 = SlotKey(fecha, "mañana", 1, 1)
        key2 = SlotKey(fecha, "mañana", 1, 2)  # Zona diferente

        assert key1 != key2

    def test_slot_key_en_set(self):
        """Verificar que SlotKey se puede usar en set."""
        fecha = date(2025, 10, 1)
        key1 = SlotKey(fecha, "mañana", 1, 1)
        key2 = SlotKey(fecha, "mañana", 1, 1)

        conjunto = {key1}
        assert key2 in conjunto


class TestFiltroProfesores:
    """Tests para el filtro de profesores."""

    def crear_profesores_test(self):
        """Crear profesores de prueba."""
        prof1 = Profesor(
            id=1, nombre_completo="Prof1", turno="mañana", zona_preferida_id=1, tutor=True
        )
        prof2 = Profesor(
            id=2, nombre_completo="Prof2", turno="tarde", zona_preferida_id=2, tutor=False
        )
        prof3 = Profesor(
            id=3, nombre_completo="Prof3", turno="mañana", zona_preferida_id=1, tutor=False
        )
        return [prof1, prof2, prof3]

    def test_crear_filtro(self):
        """Verificar que se puede crear un filtro."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)
        assert filtro is not None

    def test_filtrar_por_turno_manana(self):
        """Verificar filtrado por turno mañana."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)

        prof_manana = filtro.por_turno("mañana")
        assert len(prof_manana) == 2
        assert all(p.turno == "mañana" for p in prof_manana)

    def test_filtrar_por_turno_tarde(self):
        """Verificar filtrado por turno tarde."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)

        prof_tarde = filtro.por_turno("tarde")
        assert len(prof_tarde) == 1
        assert prof_tarde[0].turno == "tarde"

    def test_filtrar_por_zona_preferida(self):
        """Verificar filtrado por zona preferida."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)

        prof_zona1 = filtro.por_zona_preferida(1)
        assert len(prof_zona1) == 2
        assert all(p.zona_preferida_id == 1 for p in prof_zona1)

    def test_obtener_por_id(self):
        """Verificar obtención por ID."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)

        prof = filtro.por_id(2)
        assert prof is not None
        assert prof.id == 2
        assert prof.nombre_completo == "Prof2"

    def test_obtener_por_id_inexistente(self):
        """Verificar que ID inexistente retorna None."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)

        prof = filtro.por_id(999)
        assert prof is None

    def test_filtrar_por_cuota_basico(self):
        """Verificar filtrado por cuota."""
        profesores = self.crear_profesores_test()
        filtro = FiltroProfesores(profesores)

        asignadas = {1: 5, 2: 10, 3: 2}
        cuotas = {1: 10, 2: 10, 3: 10}

        # Profesores con menos de cuota completa
        resultado = filtro.filtrar_por_cuota(profesores, asignadas, cuotas)

        assert len(resultado) == 2  # Prof1 y Prof3 aún no han completado cuota
        assert all(p.id in [1, 3] for p in resultado)


class TestCacheElegibilidad:
    """Tests para la caché de elegibilidad."""

    def test_crear_cache(self):
        """Verificar que se puede crear una caché."""
        cache = CacheElegibilidad()
        assert cache is not None

    def test_cache_vacia_retorna_none(self):
        """Verificar que caché vacía retorna None."""
        cache = CacheElegibilidad()
        fecha = date(2025, 10, 1)

        resultado = cache.obtener(fecha, "mañana", 1, 1)
        assert resultado is None

    def test_guardar_y_obtener(self):
        """Verificar que se puede guardar y obtener de caché."""
        cache = CacheElegibilidad()
        fecha = date(2025, 10, 1)
        profesores_ids = [1, 2, 3]

        cache.guardar(fecha, "mañana", 1, 1, profesores_ids)
        resultado = cache.obtener(fecha, "mañana", 1, 1)

        assert resultado == profesores_ids
        assert resultado is not profesores_ids  # Debe ser copia

    def test_limpiar_cache(self):
        """Verificar que se puede limpiar la caché."""
        cache = CacheElegibilidad()
        fecha = date(2025, 10, 1)

        cache.guardar(fecha, "mañana", 1, 1, [1, 2, 3])
        cache.limpiar()

        resultado = cache.obtener(fecha, "mañana", 1, 1)
        assert resultado is None

    def test_estadisticas_cache(self):
        """Verificar estadísticas de caché."""
        cache = CacheElegibilidad()
        fecha = date(2025, 10, 1)

        # Miss
        cache.obtener(fecha, "mañana", 1, 1)
        # Guardar
        cache.guardar(fecha, "mañana", 1, 1, [1, 2])
        # Hit
        cache.obtener(fecha, "mañana", 1, 1)

        stats = cache.estadisticas()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total"] == 2
        assert stats["hit_rate"] == 50.0
        assert stats["cache_size"] == 1


class TestFuncionesAuxiliares:
    """Tests para funciones auxiliares."""

    def test_agrupar_slots_por_fecha(self):
        """Verificar agrupación de slots por fecha."""
        from dataclasses import dataclass

        @dataclass
        class SlotMock:
            fecha: date
            turno: str
            recreo: int
            zona_id: int

        fecha1 = date(2025, 10, 1)
        fecha2 = date(2025, 10, 2)

        slots = [
            SlotMock(fecha1, "mañana", 1, 1),
            SlotMock(fecha1, "mañana", 2, 1),
            SlotMock(fecha2, "mañana", 1, 1),
        ]

        grupos = agrupar_slots_por_fecha(slots)

        assert len(grupos) == 2
        assert fecha1 in grupos
        assert fecha2 in grupos
        assert len(grupos[fecha1]) == 2
        assert len(grupos[fecha2]) == 1

    def test_ordenar_profesores_equitativamente(self):
        """Verificar ordenación equitativa de profesores."""
        prof1 = Profesor(id=1, nombre_completo="Prof1", zona_preferida_id=1)
        prof2 = Profesor(id=2, nombre_completo="Prof2", zona_preferida_id=2)
        prof3 = Profesor(id=3, nombre_completo="Prof3", zona_preferida_id=1)

        profesores = [prof1, prof2, prof3]
        asignadas = {1: 5, 2: 10, 3: 2}  # Prof3 tiene menos guardias
        cuotas = {1: 10, 2: 10, 3: 10}

        ordenados = ordenar_profesores_equitativamente(profesores, asignadas, cuotas, zona_actual=1)

        # Prof3 debería estar primero (menos guardias)
        assert ordenados[0].id == 3
        # Prof1 debería estar antes que Prof2 (mismas guardias pero zona preferida)
        assert ordenados[1].id == 1

    def test_validar_indices_sincronizados(self):
        """Verificar validación de índices sincronizados."""
        fecha = date(2025, 10, 1)

        guardia1 = Guardia(fecha=fecha, turno="mañana", recreo=1, zona_id=1, profesor_id=1)

        calendario = [guardia1]
        indice = IndiceSlots.desde_calendario(calendario)

        assert validar_indices(indice, calendario)

    def test_estadisticas_rendimiento(self):
        """Verificar estadísticas de rendimiento."""
        indice = IndiceSlots()
        fecha = date(2025, 10, 1)

        indice.marcar_ocupado(fecha, "mañana", 1, 1)
        indice.marcar_ocupado(fecha, "mañana", 2, 1)

        stats = estadisticas_rendimiento(indice_slots=indice, total_slots=10)

        assert stats["slots_ocupados"] == 2
        assert stats["slots_totales"] == 10
        assert stats["cobertura"] == 20.0


class TestRendimiento:
    """Tests de rendimiento de las optimizaciones."""

    def test_indice_slots_es_rapido(self):
        """Verificar que IndiceSlots es más rápido que búsqueda lineal."""
        import time

        # Crear índice con 1000 slots
        indice = IndiceSlots()
        for i in range(1000):
            indice.marcar_ocupado(date(2025, 10, i % 30 + 1), "mañana", (i % 4) + 1, (i % 4) + 1)

        # Verificar 1000 slots
        start = time.time()
        for i in range(1000):
            indice.esta_ocupado(date(2025, 10, i % 30 + 1), "mañana", (i % 4) + 1, (i % 4) + 1)
        tiempo = time.time() - start

        # Debe ser muy rápido (< 0.01 segundos para 1000 verificaciones)
        assert tiempo < 0.01
