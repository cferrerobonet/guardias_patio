from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Profesor(Base):
    __tablename__ = 'profesores'
    id = Column(Integer, primary_key=True)
    nombre_completo = Column(String, nullable=False)  # Formato: "APELLIDOS, NOMBRE"
    email_corporativo = Column(String, nullable=True)  # Para envío de calendarios
    horas_contrato = Column(Float, nullable=False)
    porcentaje_jornada = Column(Float, nullable=False)
    turno = Column(String, nullable=False)  # mañana, tarde, completo
    tutor = Column(Boolean, default=False, nullable=False)
    fecha_inicio_guardias = Column(Date, nullable=True)
    dias_semana_permitidos = Column(Text, nullable=True)  # JSON: [0..6]
    recreos_permitidos = Column(Text, nullable=True)      # JSON: [1..N]
    guardias = relationship('Guardia', back_populates='profesor')

class Zona(Base):
    __tablename__ = 'zonas'
    id = Column(Integer, primary_key=True)
    nombre_zona = Column(String, nullable=False)
    descripcion = Column(String)
    guardias = relationship('Guardia', back_populates='zona')

class Configuracion(Base):
    __tablename__ = 'configuracion'
    id = Column(Integer, primary_key=True)
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

class Guardia(Base):
    __tablename__ = 'guardias'
    id = Column(Integer, primary_key=True)
    profesor_id = Column(Integer, ForeignKey('profesores.id'))
    fecha = Column(Date, nullable=False)
    turno = Column(String, nullable=False)
    recreo = Column(Integer, nullable=False)  # 1 o 2
    zona_id = Column(Integer, ForeignKey('zonas.id'))
    profesor = relationship('Profesor', back_populates='guardias')
    zona = relationship('Zona', back_populates='guardias')
