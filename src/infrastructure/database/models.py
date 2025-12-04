"""
SQLAlchemy ORM Models - Infrastructure Layer

Este módulo define los modelos de base de datos utilizando SQLAlchemy ORM.
Ubicación canónica según Clean Architecture: infrastructure/database/models.py

Los modelos ORM son parte de la capa de Infraestructura porque:
- Dependen de un framework específico (SQLAlchemy)
- Contienen detalles de implementación de persistencia
- Son la representación de tablas de base de datos

NOTA IMPORTANTE:
Para mantener backward compatibility, estos modelos también se exportan
desde `models.models`. Las nuevas referencias deben usar:
    from infrastructure.database.models import Profesor, Guardia, ...

O el alias más corto:
    from infrastructure.database import Profesor, Guardia, ...
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class CursoEscolar(Base):
    """
    Modelo para gestionar cursos escolares.

    Permite trabajar con múltiples cursos académicos sin perder datos históricos.
    Solo puede haber un curso activo a la vez.
    """

    __tablename__ = "cursos_escolares"

    id = Column(Integer, primary_key=True)
    anio_inicio = Column(Integer, nullable=False)  # 2024, 2025, etc.
    anio_fin = Column(Integer, nullable=False)  # 2025, 2026, etc.
    fecha_inicio = Column(Date, nullable=False)  # Por defecto 01/07/YYYY
    fecha_fin = Column(Date, nullable=False)  # Por defecto 30/06/YYYY+1
    nombre = Column(String, nullable=False)  # "Curso 2024/2025"
    activo = Column(Boolean, default=False, nullable=False)  # Solo uno activo
    cerrado = Column(Boolean, default=False, nullable=False)  # Curso finalizado
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Constraint: solo un curso puede estar activo
    __table_args__ = (UniqueConstraint("anio_inicio", "anio_fin", name="uq_anio_curso"),)

    # Relaciones
    guardias = relationship("Guardia", back_populates="curso", cascade="all, delete-orphan")


class Profesor(Base):
    """
    Modelo de profesor con todas sus propiedades.

    Atributos:
        nombre_completo: Formato "APELLIDOS, NOMBRE"
        turno: "mañana", "tarde", "completo" o "mixto"
        horas_contrato: Horas totales de contrato
        porcentaje_jornada: Porcentaje de jornada (0-100)
        horas_manana/horas_tarde: Para turno mixto
    """

    __tablename__ = "profesores"
    id = Column(Integer, primary_key=True)
    nombre_completo = Column(String, nullable=False)  # Formato: "APELLIDOS, NOMBRE"
    email_corporativo = Column(String, nullable=True)  # Para envío de calendarios
    horas_contrato = Column(Float, nullable=False)
    porcentaje_jornada = Column(Float, nullable=False)
    turno = Column(String, nullable=False)  # mañana, tarde, completo
    horas_manana = Column(Float, nullable=True)  # Horas en turno de mañana (para mixto)
    horas_tarde = Column(Float, nullable=True)  # Horas en turno de tarde (para mixto)
    tutor = Column(Boolean, default=False, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)  # Profesor activo en el sistema
    fecha_inicio_guardias = Column(Date, nullable=True)
    fecha_fin_guardias = Column(Date, nullable=True)  # Fecha límite para terminar guardias
    zona_preferida_id = Column(Integer, ForeignKey("zonas.id"), nullable=True)  # Zona preferida
    dias_semana_permitidos = Column(Text, nullable=True)  # JSON: [0..6]
    recreos_permitidos = Column(Text, nullable=True)  # JSON: [1..N]
    guardias = relationship("Guardia", back_populates="profesor")
    zona_preferida = relationship("Zona", foreign_keys=[zona_preferida_id])


class Zona(Base):
    """
    Modelo de zona de vigilancia.

    Las zonas pueden tener un periodo de operación opcional
    (fecha_inicio, fecha_fin) para zonas temporales.
    """

    __tablename__ = "zonas"
    id = Column(Integer, primary_key=True)
    nombre_zona = Column(String, nullable=False)
    descripcion = Column(String)
    fecha_inicio = Column(Date, nullable=True)  # Fecha inicio operativa (opcional)
    fecha_fin = Column(Date, nullable=True)  # Fecha fin operativa (opcional)
    guardias = relationship("Guardia", back_populates="zona")


class Configuracion(Base):
    """
    Configuración global de la aplicación.

    Almacena fechas del curso, horarios de recreos,
    ajustes de asignación y configuración de festivos.
    """

    __tablename__ = "configuracion"
    id = Column(Integer, primary_key=True)
    anio_inicio_curso = Column(Integer, nullable=False)  # Año de inicio del curso (ej: 2025)
    fecha_inicio_curso = Column(Date, nullable=False)
    fecha_fin_curso = Column(Date, nullable=False)
    hora_recreo1_manana = Column(Time, nullable=False)
    hora_recreo2_manana = Column(Time, nullable=False)
    hora_recreo1_tarde = Column(Time, nullable=True)
    hora_recreo2_tarde = Column(Time, nullable=True)
    activar_festivos_automaticos = Column(Boolean, default=True, nullable=False)
    dias_no_lectivos_personalizados = Column(Text, nullable=True)  # JSON: ["YYYY-MM-DD", ...]
    recreos_config = Column(Text, nullable=True)  # JSON: [{id, etiqueta, turno, hora, zonas}]
    ajuste_tutores = Column(Float, default=1.0, nullable=False)
    ajuste_no_tutores = Column(Float, default=1.0, nullable=False)
    algoritmo_asignacion = Column(String, default="v2.9", nullable=False)  # "v2.9" o "v3.0"
    curso_activo_id = Column(Integer, ForeignKey("cursos_escolares.id"), nullable=True)

    # Relación con curso activo
    curso_activo = relationship("CursoEscolar", foreign_keys=[curso_activo_id])


class Guardia(Base):
    """
    Modelo de guardia asignada.

    Representa la asignación de un profesor a una zona
    en una fecha, turno y recreo específicos.
    """

    __tablename__ = "guardias"
    id = Column(Integer, primary_key=True)
    # Nullable para permitir migración gradual
    curso_id = Column(Integer, ForeignKey("cursos_escolares.id"), nullable=True)
    profesor_id = Column(Integer, ForeignKey("profesores.id"))
    fecha = Column(Date, nullable=False)
    turno = Column(String, nullable=False)
    recreo = Column(Integer, nullable=False)  # 1 o 2
    zona_id = Column(Integer, ForeignKey("zonas.id"))

    # Relaciones
    curso = relationship("CursoEscolar", back_populates="guardias")
    profesor = relationship("Profesor", back_populates="guardias")
    zona = relationship("Zona", back_populates="guardias")


class Ausencia(Base):
    """
    Modelo para gestionar ausencias de profesores.

    Permite registrar periodos en los que un profesor no está disponible
    por diferentes motivos (baja médica, permiso, vacaciones, etc.).
    """

    __tablename__ = "ausencias"
    id = Column(Integer, primary_key=True)
    profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    tipo = Column(String, nullable=False)  # baja_medica, permiso, vacaciones, otros
    motivo = Column(Text, nullable=True)
    documento_path = Column(String, nullable=True)  # Ruta al justificante
    activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con Profesor
    profesor = relationship("Profesor", backref="ausencias")


# Exportar todos los modelos
__all__ = [
    "Base",
    "CursoEscolar",
    "Profesor",
    "Zona",
    "Configuracion",
    "Guardia",
    "Ausencia",
]
