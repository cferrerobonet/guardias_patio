"""Los nombres se ordenan como en un diccionario, no por código de carácter."""

from utils.orden import clave_alfabetica


def test_las_tildes_no_mandan_al_final():
    nombres = ["DOMÍNGUEZ MAS", "DÍAZ SERRANO", "Zapata", "Ávila"]
    assert sorted(nombres, key=clave_alfabetica) == [
        "Ávila", "DÍAZ SERRANO", "DOMÍNGUEZ MAS", "Zapata",
    ]


def test_la_ene_va_entre_la_n_y_la_o():
    assert sorted(["Ochoa", "Núñez", "Nuno", "Nzz"], key=clave_alfabetica) == [
        "Nuno", "Núñez", "Nzz", "Ochoa",
    ]


def test_sin_texto_no_falla():
    assert clave_alfabetica(None) == ""
