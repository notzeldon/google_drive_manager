from aiohttp import web
from aiohttp_session import get_session

from manager.api.links import get_client_id_file, SCOPES


async def authorize_middleware(app, handler):

    async def middleware(request):
        def check_path(path):
            result = True
            for r in ['/login', '/register', '/logout', '/api', '/auth', '/oauth']:
                if path.startswith(r):
                    result = False
            if path == '/':
                result = False
            return result

        session = await get_session(request)

        # Если есть данные о пользователе в сессии, то вызываем обработчик
        if session.get("user"):
            return await handler(request)

        # Если нет, то это неизвестный пользователь. Если URL для авторизованных, просим залогиниться
        elif check_path(request.path):
            url = request.app.router['login'].url_for()
            raise web.HTTPFound(url)

        # Остальное - отдаем как есть
        else:
            return await handler(request)

    return middleware


async def google_drive_middleware(app, handler):

    async def middleware(request):
        session = await get_session(request)

        def check_path(path):
            for r in ['/auth', '/oauth']:
                if path.startswith(r):
                    return False
            return True

        if check_path(request.path):
            return await handler(request)

        if 'credentials' not in session:
            raise web.HTTPFound(request.app.router['authorize'].url_for())

        else:
            return await handler(request)

    return middleware

