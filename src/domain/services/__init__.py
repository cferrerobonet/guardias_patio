"""
Domain Services — actualmente vacío.

Los servicios que antes vivían aquí (AsignacionGuardiaService,
DisponibilidadProfesorService, DistribucionCuotasService, EquidadGuardiasService)
han sido movidos a src/services/ porque dependen directamente de infraestructura
(SQLAlchemy Session) y no pertenecen al dominio puro.
"""
