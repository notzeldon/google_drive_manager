import argparse

from aiohttp import web
import asyncio

from manager import create_app
from manager.settings import load_config

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    print('Library uvloop is not available')

parser = argparse.ArgumentParser(description='Manager project')
parser.add_argument('--host', help='Host to listen', default='0.0.0.0')
parser.add_argument('--port', help='Port to accept connections', default=8080)
parser.add_argument('--reload', action='store_true', help='Autoreload code on change')
parser.add_argument('-c', '--config', type=argparse.FileType('r'), help='Path to config file')

parser.add_argument('--noauth_local_webserver', action='store_true', help='')

args = parser.parse_args()

app = create_app(config=load_config(args.config))

if args.reload:
    print('Start with code reload')
    import aioreloader
    aioreloader.start()

if __name__ == '__main__':
    def run():
        # ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # ssl_context.load_cert_chain('domain_srv.crt', 'domain_srv.key')

        web.run_app(app, host=args.host, port=args.port)

