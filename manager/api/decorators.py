from aiohttp import web
from aiohttp_session import get_session


def auth_required(func):
    async def wrapper(request):
        request.app['session'] = session = await get_session(request)
        error = f'Login via {request.app.router["api_user_auth"].url_for()}'
        if 'user' not in session or not session['user']:
            return web.json_response(
                status=401,
                data=dict(error=error)
            )
        return await func(request)
    return wrapper

