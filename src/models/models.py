from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Profesor(Base):
    __tablename__ = 'profesores'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    horas_contrato = Column(Float, nullable=False)
    porcentaje_jornada = Column(Float, nullable=False)
    turno = Column(String, nullable=False)  # mañana, tarde, completo
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
