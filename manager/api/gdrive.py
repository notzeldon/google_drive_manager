import google_auth_oauthlib
from aiohttp import web
from aiohttp_session import get_session

from manager.api.links import get_client_id_file


async def oauth2callback(request):
    session = await get_session()

    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        get_client_id_file(),
        scopes=['https://www.googleapis.com/auth/drive'],
        state=state)
    flow.redirect_uri = 'https://gdt-manager.herokuapp.com/oauth2callback'

    authorization_response = 'https://gdt-manager.herokuapp.com/oauth2callback'
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return web.HTTPFound('/')