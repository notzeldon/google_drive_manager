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


async def create_app(config: dict or None = None):

    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)

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
    app['db'] = await asyncpgsa.create_pool(dsn=os.environ.get('DATABASE_URL'))


async def on_shutdown(app):
    await app['db'].close()
