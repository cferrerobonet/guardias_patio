"""
API REST - Dependency Injection

Gestiona las dependencias de la API, principalmente la sesión de base de datos.
"""

from typing import Generator

from sqlalchemy.orm import Session

from database.db_manager import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos.

    Yields:
        Session: Sesión de SQLAlchemy

    Examples:
        >>> @app.get("/items")
        >>> def read_items(db: Session = Depends(get_db)):
        >>>     return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
