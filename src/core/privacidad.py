"""Enmascarado de datos personales para los registros (PRIV-002).

Los ficheros de `logs/` se guardan meses y se adjuntan a un informe de
diagnóstico sin mirarlos. Un correo o un nombre completo no aportan nada para
depurar y sí identifican a una persona.
"""


def enmascarar_correo(correo) -> str:
    """`ana.garcia@epla.es` → `a***@epla.es`; sin arroba, sólo la inicial."""
    texto = str(correo or "").strip()
    if not texto:
        return "(sin correo)"
    usuario, arroba, dominio = texto.partition("@")
    inicial = usuario[:1] if usuario else "*"
    return f"{inicial}***@{dominio}" if arroba else f"{inicial}***"


def enmascarar_nombre(nombre) -> str:
    """`García López, Ana` → `G. L., A.`: iniciales, suficientes para seguir un rastro."""
    texto = str(nombre or "").strip()
    if not texto:
        return "(sin nombre)"
    partes = []
    for trozo in texto.split(","):
        iniciales = " ".join(f"{p[0]}." for p in trozo.split() if p)
        if iniciales:
            partes.append(iniciales)
    return ", ".join(partes)
