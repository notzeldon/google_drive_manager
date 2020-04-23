from . import api
from .api import gdrive
from .views import frontend

def setup_routes(app):

    app.router.add_route('GET', '/', frontend.index, name='main')
    app.router.add_route('GET', '/register', frontend.Register, name="register")
    app.router.add_route('GET', '/login', frontend.Login, name='login')
    app.router.add_route('GET', '/change-password', frontend.ChangePassword, name='change_password')
    app.router.add_route('GET', '/delete', frontend.Delete, name='delete')
    app.router.add_route('GET', '/panel', frontend.UserPanel, name='panel')

    # API

    app.router.add_route('*', '/oauth2callback', gdrive.oauth2callback, name='oauth2callback')


    app.router.add_route('GET', r'/api/user', api.users.user_info, name='api_user_info')
    app.router.add_route('POST', r'/api/user/register', api.users.user_register, name='api_user_register')
    app.router.add_route('POST', r'/api/user/auth', api.users.user_auth, name='api_user_auth')
    app.router.add_route('POST', r'/api/user/change-password', api.users.user_change_password, name='api_user_change_password')
    app.router.add_route('GET', r'/api/user/delete', api.users.user_delete, name='api_user_delete')
    app.router.add_route('GET', r'/api/user/logout', api.users.user_logout, name='api_user_logout')

    app.router.add_route('GET', r'/api/links', api.links.links_list, name='api_links_list')
    app.router.add_route('POST', r'/api/links/add', api.links.links_add, name='api_links_add')
    app.router.add_route('GET', r'/api/links/delete', api.links.links_delete, name='api_links_delete')
    app.router.add_route('GET', r'/api/links/download', api.links.links_download, name='api_links_download')





