from aiohttp import web
from aiohttp_session import get_session

from manager.api.links import get_client_id_file, SCOPES


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

        # Остальное - отдаем как есть
        else:
            return await handler(request)

    return middleware


async def google_drive_middleware(app, handler):

    async def middleware(request):

        def check_path(path):
            result = True
            for r in ['/oauth2callback']:
                if path.startswith(r):
                    result = False
            return result

        if not check_path(request.path):
            import google_auth_oauthlib.flow

            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(get_client_id_file(), SCOPES)

            flow.redirect_uri = 'http://gdt-manager.herokuapp.com/oauth2callback'

            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true')

            raise web.HTTPFound(authorization_url)

        else:
            return await handler(request)

    return middleware

