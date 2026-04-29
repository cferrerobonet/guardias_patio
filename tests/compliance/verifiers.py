"""
ComplianceVerifier — verifica el cumplimiento de restricciones de asignación.

Cada método check_rN() verifica una restricción específica y devuelve un
ConstraintResult con el porcentaje de cumplimiento y la lista de fallos.

Uso:
    verifier = ComplianceVerifier(profesores, guardias, session)
    result = verifier.check_r1_turno()
    all_results = verifier.run_all()
    verifier.print_report()
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional


@dataclass
class ConstraintResult:
    """Resultado de verificar una restricción."""

    restriccion: str
    tipo: str  # "DURA" | "BLANDA"
    total_evaluadas: int
    cumplidas: int
    fallos: list[str] = field(default_factory=list)
    cumplimiento_pct: float = 0.0

    def __post_init__(self):
        if self.total_evaluadas > 0:
            self.cumplimiento_pct = self.cumplidas / self.total_evaluadas * 100.0
        else:
            self.cumplimiento_pct = 100.0


class ComplianceVerifier:
    """
    Verifica el cumplimiento de restricciones sobre una lista de guardias generadas.

    Args:
        profesores: lista de Profesor ORM obtenida antes de ejecutar el algoritmo
        guardias: lista de Guardia devuelta por el algoritmo
        session: sesión SQLAlchemy (necesaria para consultas de ausencias)
    """

    def __init__(self, profesores, guardias, session):
        self.profesores = profesores
        self.guardias = guardias
        self.session = session
        self._prof_map = {p.id: p for p in profesores}

    # ------------------------------------------------------------------
    # R1 — Turno compatible
    # ------------------------------------------------------------------

    def check_r1_turno(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p:
                continue
            total += 1
            turno_libre = p.turno in ("completo", "mixto", "ambos")
            if turno_libre or p.turno == g.turno:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo} (turno={p.turno}) asignado en '{g.turno}' el {g.fecha}"
                )
        return ConstraintResult("R1_turno", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R2 — No ausente en fecha
    # ------------------------------------------------------------------

    def check_r2_ausencias(self) -> ConstraintResult:
        from infrastructure.database.models import Ausencia

        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p:
                continue
            total += 1
            ausente = (
                self.session.query(Ausencia)
                .filter(
                    Ausencia.profesor_id == g.profesor_id,
                    Ausencia.fecha_inicio <= g.fecha,
                    Ausencia.fecha_fin >= g.fecha,
                    Ausencia.activa == True,  # noqa: E712
                )
                .first()
            )
            if ausente:
                fallos.append(
                    f"{p.nombre_completo} ausente el {g.fecha} pero asignado (ausencia {ausente.id})"
                )
            else:
                cumplidas += 1
        return ConstraintResult("R2_ausencias", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R3 — Fecha >= fecha_inicio_guardias
    # ------------------------------------------------------------------

    def check_r3_fecha_inicio(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p or not p.fecha_inicio_guardias:
                continue
            total += 1
            if g.fecha >= p.fecha_inicio_guardias:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo}: guardia el {g.fecha} antes de inicio {p.fecha_inicio_guardias}"
                )
        return ConstraintResult("R3_fecha_inicio", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R4 — Fecha <= fecha_fin_guardias
    # ------------------------------------------------------------------

    def check_r4_fecha_fin(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p or not p.fecha_fin_guardias:
                continue
            total += 1
            if g.fecha <= p.fecha_fin_guardias:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo}: guardia el {g.fecha} después de fin {p.fecha_fin_guardias}"
                )
        return ConstraintResult("R4_fecha_fin", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R5 — Recreo en lista simple permitida
    # ------------------------------------------------------------------

    def check_r5_recreos_lista(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p or not p.recreos_permitidos:
                continue
            recreos = self._parse_json(p.recreos_permitidos, [])
            if not isinstance(recreos, list):
                continue  # Es dict → cubre R6
            total += 1
            if g.recreo in recreos:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo}: recreo {g.recreo} no está en {recreos} el {g.fecha}"
                )
        return ConstraintResult("R5_recreos_lista", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R6 — Recreo en dict por día
    # ------------------------------------------------------------------

    def check_r6_recreos_dict(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p or not p.recreos_permitidos:
                continue
            recreos = self._parse_json(p.recreos_permitidos, {})
            if not isinstance(recreos, dict):
                continue  # Es lista → cubre R5
            total += 1
            dia_key = str(g.fecha.weekday())
            permitidos_dia = recreos.get(dia_key, [])
            if g.recreo in permitidos_dia:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo}: recreo {g.recreo} no permitido el {g.fecha} "
                    f"(dia={dia_key}, permitidos={permitidos_dia})"
                )
        return ConstraintResult("R6_recreos_dict", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R7 — Día de semana permitido
    # ------------------------------------------------------------------

    def check_r7_dias_semana(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0
        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p or not p.dias_semana_permitidos:
                continue
            dias = self._parse_json(p.dias_semana_permitidos, list(range(7)))
            if not isinstance(dias, list):
                continue
            total += 1
            if g.fecha.weekday() in dias:
                cumplidas += 1
            else:
                nombre_dia = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][g.fecha.weekday()]
                fallos.append(
                    f"{p.nombre_completo}: asignado el {g.fecha} ({nombre_dia}), "
                    f"pero solo puede en días {dias}"
                )
        return ConstraintResult("R7_dias_semana", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R8 — Máximo 1 guardia por día por profesor
    # ------------------------------------------------------------------

    def check_r8_max_guardia_dia(self) -> ConstraintResult:
        por_prof_dia: dict[tuple, list] = defaultdict(list)
        for g in self.guardias:
            por_prof_dia[(g.profesor_id, g.fecha)].append(g)

        fallos = []
        cumplidas = 0
        total = len(por_prof_dia)

        for (prof_id, fecha), gs in por_prof_dia.items():
            if len(gs) <= 1:
                cumplidas += 1
            else:
                p = self._prof_map.get(prof_id)
                name = p.nombre_completo if p else str(prof_id)
                fallos.append(f"{name}: {len(gs)} guardias el {fecha}")

        return ConstraintResult("R8_max_guardia_dia", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R9 — No simultaneidad (mismo prof, fecha, turno, recreo)
    # ------------------------------------------------------------------

    def check_r9_no_simultaneidad(self) -> ConstraintResult:
        momentos: dict[tuple, int] = defaultdict(int)
        for g in self.guardias:
            momentos[(g.profesor_id, g.fecha, g.turno, g.recreo)] += 1

        fallos = []
        cumplidas = 0
        total = len(momentos)

        for (prof_id, fecha, turno, recreo), count in momentos.items():
            if count <= 1:
                cumplidas += 1
            else:
                p = self._prof_map.get(prof_id)
                name = p.nombre_completo if p else str(prof_id)
                fallos.append(
                    f"{name}: {count} zonas simultáneas el {fecha} turno {turno} recreo {recreo}"
                )

        return ConstraintResult("R9_no_simultaneidad", "DURA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R10 — Zona preferida respetada (BLANDA)
    # ------------------------------------------------------------------

    def metric_r10_zona_preferida(self) -> ConstraintResult:
        fallos = []
        cumplidas = 0
        total = 0

        for g in self.guardias:
            p = self._prof_map.get(g.profesor_id)
            if not p or not p.zona_preferida_id:
                continue
            total += 1
            if g.zona_id == p.zona_preferida_id:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo}: zona {g.zona_id} ≠ preferida {p.zona_preferida_id} el {g.fecha}"
                )

        return ConstraintResult("R10_zona_preferida", "BLANDA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R11 — Equidad proporcional a jornada (BLANDA)
    # ------------------------------------------------------------------

    def metric_r11_equidad(self) -> ConstraintResult:
        guardias_count: dict[int, int] = defaultdict(int)
        for g in self.guardias:
            guardias_count[g.profesor_id] += 1

        total_jornada = sum(p.porcentaje_jornada for p in self.profesores) or 1.0
        total_guardias = len(self.guardias) or 0

        fallos = []
        cumplidas = 0
        total = len(self.profesores)

        for p in self.profesores:
            expected_pct = p.porcentaje_jornada / total_jornada
            expected = expected_pct * total_guardias
            actual = guardias_count.get(p.id, 0)
            if expected <= 0:
                cumplidas += 1
                continue
            deviation = abs(actual - expected) / expected * 100.0
            if deviation <= 15.0:
                cumplidas += 1
            else:
                fallos.append(
                    f"{p.nombre_completo}: esperado≈{expected:.1f}, "
                    f"actual={actual}, desv={deviation:.1f}%"
                )

        return ConstraintResult("R11_equidad", "BLANDA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R12 — Ajuste tutor/no-tutor (BLANDA)
    # ------------------------------------------------------------------

    def metric_r12_ajuste_tutor(
        self, ajuste_tutores: float = 1.0, ajuste_no_tutores: float = 1.0
    ) -> ConstraintResult:
        """
        Verifica que el ratio real de guardias tutor/no-tutor es coherente con
        los factores de ajuste configurados (±5% de tolerancia).
        """
        tutores = [p for p in self.profesores if p.tutor]
        no_tutores = [p for p in self.profesores if not p.tutor]

        if not tutores or not no_tutores:
            return ConstraintResult("R12_ajuste_tutor", "BLANDA", 0, 0, [], 100.0)

        guardias_count: dict[int, int] = defaultdict(int)
        for g in self.guardias:
            guardias_count[g.profesor_id] += 1

        media_tutor = sum(guardias_count.get(p.id, 0) for p in tutores) / len(tutores)
        media_no_tutor = sum(guardias_count.get(p.id, 0) for p in no_tutores) / len(no_tutores)

        fallos = []
        cumplidas = 0
        total = 1

        if media_no_tutor <= 0:
            return ConstraintResult("R12_ajuste_tutor", "BLANDA", 0, 0, [], 100.0)

        ratio_real = media_tutor / media_no_tutor
        ratio_esperado = ajuste_tutores / ajuste_no_tutores
        desviacion = abs(ratio_real - ratio_esperado) / max(ratio_esperado, 0.001) * 100.0

        if desviacion <= 5.0:
            cumplidas = 1
        else:
            fallos.append(
                f"Ratio real tutor/no-tutor={ratio_real:.3f}, "
                f"esperado={ratio_esperado:.3f}, desv={desviacion:.1f}%"
            )

        return ConstraintResult("R12_ajuste_tutor", "BLANDA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # R13 — Consecutividad temporal (BLANDA)
    # ------------------------------------------------------------------

    def metric_r13_consecutividad(self) -> ConstraintResult:
        """
        Mide qué % de profesores tienen ≥60% de sus días de guardia
        agrupados en rachas consecutivas (≥2 días seguidos).
        """
        prof_dates: dict[int, set[date]] = defaultdict(set)
        for g in self.guardias:
            prof_dates[g.profesor_id].add(g.fecha)

        fallos = []
        cumplidas = 0
        total = len(prof_dates)

        for prof_id, fechas in prof_dates.items():
            sorted_dates = sorted(fechas)
            if len(sorted_dates) < 2:
                cumplidas += 1
                continue

            en_bloque = 0
            for i, fecha in enumerate(sorted_dates):
                prev = sorted_dates[i - 1] if i > 0 else None
                nxt = sorted_dates[i + 1] if i < len(sorted_dates) - 1 else None
                prev_consec = prev is not None and (fecha - prev).days == 1
                next_consec = nxt is not None and (nxt - fecha).days == 1
                if prev_consec or next_consec:
                    en_bloque += 1

            pct = en_bloque / len(sorted_dates) * 100.0
            if pct >= 60.0:
                cumplidas += 1
            else:
                p = self._prof_map.get(prof_id)
                name = p.nombre_completo if p else str(prof_id)
                fallos.append(f"{name}: {pct:.1f}% días en bloque (mín 60%)")

        return ConstraintResult("R13_consecutividad", "BLANDA", total, cumplidas, fallos)

    # ------------------------------------------------------------------
    # run_all / print_report
    # ------------------------------------------------------------------

    def run_all(self) -> list[ConstraintResult]:
        return [
            self.check_r1_turno(),
            self.check_r2_ausencias(),
            self.check_r3_fecha_inicio(),
            self.check_r4_fecha_fin(),
            self.check_r5_recreos_lista(),
            self.check_r6_recreos_dict(),
            self.check_r7_dias_semana(),
            self.check_r8_max_guardia_dia(),
            self.check_r9_no_simultaneidad(),
            self.metric_r10_zona_preferida(),
            self.metric_r11_equidad(),
            self.metric_r12_ajuste_tutor(),
            self.metric_r13_consecutividad(),
        ]

    def print_report(self) -> None:
        results = self.run_all()
        header = f"{'Restricción':<25} {'Tipo':<6} {'Total':>6} {'OK':>6} {'%':>7} {'Estado'}"
        print("\n" + "=" * 70)
        print("COMPLIANCE REPORT")
        print("=" * 70)
        print(header)
        print("-" * 70)
        for r in results:
            estado = "✅" if r.cumplimiento_pct >= (100.0 if r.tipo == "DURA" else 50.0) else "❌"
            print(
                f"{r.restriccion:<25} {r.tipo:<6} {r.total_evaluadas:>6} "
                f"{r.cumplidas:>6} {r.cumplimiento_pct:>6.1f}% {estado}"
            )
            for fallo in r.fallos[:3]:
                print(f"  {'':25}  → {fallo}")
            if len(r.fallos) > 3:
                print(f"  {'':25}  → ... y {len(r.fallos) - 3} más")
        print("=" * 70)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(value: Optional[str], default: Any) -> Any:
        if not value:
            return default
        try:
            result = json.loads(value)
            return result if isinstance(result, (list, dict)) else default
        except (json.JSONDecodeError, TypeError):
            return default
