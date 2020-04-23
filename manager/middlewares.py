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
            return await handler(request)

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

        session = await get_session(request)


        if not check_path(request.path):
            pass
            import google.oauth2.credentials
            import google_auth_oauthlib.flow

            # Use the client_secret.json file to identify the application requesting
            # authorization. The client ID (from that file) and access scopes are required.

            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(get_client_id_file(), SCOPES)

            # Indicate where the API server will redirect the user after the user completes
            # the authorization flow. The redirect URI is required. The value must exactly
            # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
            # configured in the API Console. If this value doesn't match an authorized URI,
            # you will get a 'redirect_uri_mismatch' error.
            # TODO: Change
            flow.redirect_uri = 'https://gdt-manager.herokuapp.com/oauth2callback'

            # Generate URL for request to Google's OAuth 2.0 server.
            # Use kwargs to set optional request parameters.
            authorization_url, state = flow.authorization_url(
                # Enable offline access so that you can refresh an access token without
                # re-prompting the user for permission. Recommended for web server apps.
                access_type='offline',
                # Enable incremental authorization. Recommended as a best practice.
                include_granted_scopes='true')

            raise web.HTTPFound(authorization_url)
            return await handler(request)

        return await handler(request)

    return middleware

