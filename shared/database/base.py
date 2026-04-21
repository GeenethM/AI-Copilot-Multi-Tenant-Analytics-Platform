"""
base.py
───────
SQLAlchemy declarative base that all database models extend.

Keeping the Base in its own file prevents circular imports — every model
imports Base from here, and the connection module imports models only when
needed (e.g. for Alembic autogenerate).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    All ORM models inherit from this class.
    SQLAlchemy uses it to track every table definition for migrations.
    """
    pass
