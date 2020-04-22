import hashlib

import bcrypt
from aiohttp import web
from aiohttp_session import get_session

from manager import db
from manager.api.decorators import auth_required


async def get_salted_pwd(pwd, salt):
    return hashlib.md5((pwd + salt).encode('utf-8')).hexdigest()


async def get_user_record(request, email=None, user_id=None):
    if not email and not user_id:
        return

    async with request.app['db'].acquire() as conn:
        cond = db.users.c.email == email if email else db.users.c.id == user_id
        query = db.users.select().where(cond).limit(1)
        result = await conn.fetch(query)

    if result:
        return result[0]


async def user_register(request):
    data = await request.post()
    for i in ('email', 'password'):
        if i not in data:
            return web.json_response(
                status=400,
                data=dict(error='Required fields: "email", "password"'),
            )

    email = data['email']
    pwd = data['password']

    result = await get_user_record(request, email=email)

    if result:
        return web.json_response(status=400, data=dict(error='Cannot use this email'))

    salt = bcrypt.gensalt().decode('ascii')
    salted_pwd = await get_salted_pwd(pwd, salt)

    async with request.app['db'].acquire() as conn:
        query = db.users.insert().values(email=email, password=salted_pwd, salt=salt)
        result = await conn.fetch(query)

    return web.Response(status=201)


async def user_auth(request):

    data = await request.post()
    for i in ('email', 'password'):
        if i not in data:
            return web.json_response(
                status=400,
                data=dict(error='Required fields: "email", "password"'),
            )

    email = data['email']
    pwd = data['password']

    result = await get_user_record(request, email=email)

    if result:
        user = result
        salted_pwd = await get_salted_pwd(pwd, user['salt'])

        if user['password'] != salted_pwd:
            result = False

        else:
            session = await get_session(request)
            session['user'] = user['id']

    if not result:
        return web.json_response(
            status=400,
            data=dict(error='Email or password is wrong or user does not exists')
        )

    return web.Response()


@auth_required
async def user_change_password(request):
    data = await request.post()
    session = request.app['session']

    for i in ('old_password', 'password', 'password2'):
        if i not in data:
            return web.json_response(
                status=400,
                data=dict(error='Required fields: "old_password", "password", "password2"'),
            )

    old_pwd = data['old_password']
    pwd = data['password']
    pwd2 = data['password2']

    if pwd != pwd2:
        return web.json_response(
            status=400,
            data=dict(error='Password do not match'),
        )

    if pwd == old_pwd:
        return web.json_response(
            status=400,
            data=dict(error='Old and new passwords equals'),
        )

    result = await get_user_record(request, user_id=session['user'])

    if not result:
        return web.json_response(
            status=400,
            data=dict(error='User do not exists'),
        )
    else:
        user = result
        salted_pwd = await get_salted_pwd(old_pwd, user['salt'])

        if user['password'] != salted_pwd:
            return web.json_response(
                status=400,
                data=dict(error='Wrong old password'),
            )

    async with request.app['db'].acquire() as conn:
        new_salt = bcrypt.gensalt().decode('ascii')
        salted_pwd = await get_salted_pwd(pwd, new_salt)
        query = db.users.update().values(password=salted_pwd, salt=new_salt).where(db.users.c.id == session['user'])
        result = await conn.fetch(query)

    return web.Response()

@auth_required
async def user_delete(request):
    data = await request.post()
    session = request.app['session']

    async with request.app['db'].acquire() as conn:
        query = db.links.delete().where(db.links.c.user_id == session['user'])
        result = await conn.fetch(query)
        query = db.users.delete().where(db.users.c.id == session['user'])
        result = await conn.fetch(query)

    session['user'] = None

    return web.Response()


@auth_required
async def user_info(request):
    session = request.app['session']

    user = await get_user_record(user_id=session['user'])

    return web.json_response(
        data=dict(
            email=user['email']
        )
    )


@auth_required
async def user_logout(request):
    session = request.app['session']
    session.pop('user')

    return web.Response()




