import os

from sqlalchemy import (
    Table, Text, Integer, VARCHAR, MetaData, Column,
    ForeignKey, String, create_engine)

__all__ = ('users', 'links',)

meta = MetaData()

users = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('email', String, nullable=False),
    Column('password', String, nullable=False),
    Column('salt', String, nullable=False),
)

links = Table(
    'links', meta,
    Column('id', Integer, primary_key=True),
    Column('title', String, nullable=False),
    Column('file_id', String, nullable=False),
    Column('user_id', None, ForeignKey('users.id')),
)


# engine = create_engine(os.environ.get("DATABASE_URL"))
# meta.create_all(engine)
