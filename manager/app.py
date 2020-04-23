import base64
import os

import asyncpgsa
from aiohttp import web

from cryptography import fernet
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

import aiohttp_jinja2, jinja2

from .middlewares import authorize_middleware
from .routes import setup_routes


import argparse
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--noauth_local_webserver', action='store_true',
                    default=False, help='Do not run a local web server.')


async def create_app(config=None):

    secret_key = b'3d\xa9Na\xaa\x84 \xa7\x0f\xe4\x08\x1esd\xfc\xe8\x8a\x1e,R\x8c\xf4\xdc\xccO\xf3;\x12\x95\xc8('

    app = web.Application(middlewares=[
        session_middleware(EncryptedCookieStorage(secret_key)),
        authorize_middleware,
    ])

    app['config'] = config or dict()
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader('manager', 'templates'),
    )

    setup_routes(app)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_shutdown)

    return app


async def on_start(app):
    app['db'] = await asyncpgsa.create_pool(dsn=os.environ.get('DATABASE_URL'), min_size=1, max_size=5)


async def on_shutdown(app):
    await app['db'].close()
