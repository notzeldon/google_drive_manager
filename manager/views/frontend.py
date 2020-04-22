from aiohttp import web
from aiohttp_jinja2 import template
from aiohttp_session import get_session


@template('index.html')
async def index(request):
    return {}




class Register(web.View):

    @template('users/register.html')
    async def get(self):
        return {}


class Login(web.View):

    @template('users/login.html')
    async def get(self):
        return {}


class ChangePassword(web.View):

    @template('change_password.html')
    async def get(self):
        return {}


class Delete(web.View):

    @template('delete.html')
    async def get(self):
        return {}


class UserPanel(web.View):

    @template('users/panel.html')
    async def get(self):
        return {}
