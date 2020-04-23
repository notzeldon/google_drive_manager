import io
import mimetypes
import os
import os.path
import re
import shutil

from aiohttp import web
from googleapiclient.discovery import build
# If modifying these scopes, delete the file token.pickle.
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import Http
from multidict import MultiDict
from oauth2client import file, client, tools

from manager import db
from manager.api.decorators import auth_required

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata',
]


def get_gdrive_service(tmp_dir):
    store = file.Storage(os.path.join(tmp_dir, 'storage.json'))
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_id.json', SCOPES)
        creds = tools.run_flow(flow, store)
    return build('drive', 'v3', http=creds.authorize(Http()))


def get_file_id(link: str):
    # https://docs.google.com/document/d/1z7REbPTIrI66PsdloDRkHTT7mviqjoMW3gT1p1JDy1s/edit?usp=sharing
    if not link.startswith('https://docs.google.com/document/d/'):
        return
    match = re.search(r'(?<=d\/)([^\/])+', link)
    if match:
        return match.group(0)


async def get_file_meta(file_id, tmp_dir):
    service = get_gdrive_service(tmp_dir)

    return service.files().get(fileId=file_id).execute()



async def get_file(file_id, tmp_dir, user_id):
    service = get_gdrive_service(tmp_dir)

    # Инфа о форматах для экспорта
    formats = service.about().get(fields='exportFormats').execute()
    formats = formats['exportFormats']

    # Инфа о файле
    result = service.files().get(fileId=file_id).execute()

    export_mimetype = formats[result['mimeType']][0] if result['mimeType'] in formats else result['mimeType']
    extension = mimetypes.guess_extension(export_mimetype)

    req = service.files().export_media(fileId=file_id, mimeType=export_mimetype)

    dir_ = tmp_dir
    if user_id:
        dir_ = os.path.join(tmp_dir, str(user_id))
        if not os.path.exists(dir_):
            os.mkdir(dir_)

    filename = os.path.join(dir_, result['name'] + extension)

    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    return filename, done


@auth_required
async def links_list(request):
    data = request.query
    session = request.app['session']

    paginate_by = 'paginate_by' in data and data['paginate_by'].isdigit() and int(data['paginate_by']) or 50
    page = 'p' in data and data['p'].isdigit() and int(data['p']) or 0

    async with request.app['db'].acquire() as conn:
        query = db.links.select().where(
            db.links.c.user_id == session['user'],
        ).order_by(db.links.c.title).limit(paginate_by + 1)
        if page:
            query = query.offset(page * paginate_by)

        result = await conn.fetch(query)

    links = []
    next_page = False
    prev_page = page > 0
    counter = 0
    for r in result:
        counter += 1
        if counter > paginate_by:
            next_page = True
            break

        links.append(
            dict(
                id=r['id'],
                title=r['title'],
                download_link=str(request.app.router['api_links_download'].url_for().with_query(id=r['id'])),
                delete_link=str(request.app.router['api_links_delete'].url_for().with_query(id=r['id'])),
            )
        )

    return web.json_response(
        data=dict(
            next=next_page and str(request.app.router['api_links_list'].url_for().with_query(p=page + 1, paginate_by=paginate_by)),
            prev=prev_page and str(request.app.router['api_links_list'].url_for().with_query(p=page - 1, paginate_by=paginate_by)),
            files=links,
        )
    )






@auth_required
async def links_add(request):
    data = await request.post()
    session = request.app['session']
    tmp_dir = request.app['config'].get('tmp_dir', '.')

    file_id = get_file_id(data['link'])
    if not file_id:
        return web.json_response(
            status=400,
            data=dict(error='It is not Google Drive file link')
        )

    # TODO: Хранить ID и мета данные
    file_meta = await get_file_meta(file_id=file_id, tmp_dir=tmp_dir)

    title = file_meta.get('name')
    if not title:
        return web.json_response(
            status=400,
            data=dict(error='Cannot get file name'),
        )

    async with request.app['db'].acquire() as conn:
        query = db.links.insert().values(
            title=title,
            file_id=file_id,
            user_id=session['user'],
        )
        result = await conn.fetch(query)

    return web.Response()


@auth_required
async def links_delete(request):
    data = request.query
    session = request.app['session']

    db_file_id = data['id']
    if db_file_id.isdigit():
        db_file_id = int(db_file_id)
    else:
        return web.json_response(
            status=400,
            data=dict(error='Wrong file link ID')
        )

    async with request.app['db'].acquire() as conn:
        query = db.links.delete().where(
            db.links.c.id == db_file_id,
        ).where(
            db.links.c.user_id == session['user'],
        )
        result = await conn.fetch(query)

    return web.Response()


@auth_required
async def links_download(request):

    data = request.query
    session = request.app['session']
    tmp_dir = request.app['config'].get('tmp_dir', '.')

    files_ids = []

    async with request.app['db'].acquire() as conn:
        if 'id' in data:

            id = data['id']
            if id.isdigit():
                id = int(id)
            else:
                return web.json_response(
                    status=400,
                    data=dict(error='File id must be integer'),
                )

            query = db.links.select().where(
                db.links.c.user_id == session['user']
            ).where(
                db.links.c.id == id
            )
            result = await conn.fetch(query)
            if result[0]['file_id']:
                files_ids.append(result[0]['file_id'])
        else:
            query = db.links.select().where(db.links.c.user_id == session['user'])
            result = await conn.fetch(query)
            for r in result:
                files_ids.append(r['file_id'])

    res_list = []

    for file_id in files_ids:
        res = await get_file(file_id, tmp_dir, session.get('user'))
        res_list.append(res)

    if len(res_list) == 1:
        file_name = res_list[0][0]
    else:
        file_name = os.path.join(tmp_dir, f'files_{session.get("user")}.zip')
        shutil.make_archive(file_name, 'zip', os.path.join(tmp_dir, str(session.get('user'))))
        file_name += '.zip'

    # TODO: Это можно сделать лучше
    with open(file_name, 'rb') as f:
        content = f.read()
        response = web.Response(
            body=content,
            headers=MultiDict({
                'Content-Disposition': 'attachment; filename="%s"' % file_name.split('/')[-1],
            })
        )

    if '.zip' not in file_name:
        os.remove(file_name)
    else:
        os.remove(file_name)
        shutil.rmtree(os.path.join(tmp_dir, str(session.get('user'))))

    return response

