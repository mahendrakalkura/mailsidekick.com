# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, event, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import Pool
from sqlalchemy.schema import ThreadLocalMetaData

import settings


def to_dictionary(instance):
    dictionary = {}
    for column in instance.__table__.columns:
        dictionary[column.name] = getattr(instance, column.name)
    return dictionary


@event.listens_for(Pool, 'checkout')
def ping_connection(connection, record, proxy):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        raise exc.DisconnectionError()
    cursor.close()

engine = create_engine(
    settings.SQLALCHEMY,
    convert_unicode=True,
    echo=False,
    pool_recycle=15,
    pool_size=25,
    pool_timeout=15,
    strategy='threadlocal'
)
base = declarative_base(bind=engine, metadata=ThreadLocalMetaData())
base.to_dictionary = to_dictionary
