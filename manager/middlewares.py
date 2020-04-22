from aiohttp import web
from aiohttp_session import get_session


async def authorize_middleware(app, handler):

    async def middleware(request):
        def check_path(path):
            result = True
            for r in ['/login', '/register', '/logout', '/api']:
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
            return handler(request)

        # Остальное - отдаем как есть
        else:
            return await handler(request)

    return middleware

