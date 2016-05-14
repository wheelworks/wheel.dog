import asyncio as aio
import os
import pprint
import sys
import signal

import aiohttp
from aiohttp import web


def terminate(loop):
    print('Terminating')

    loop.stop()


async def create_image(request):
    name = request.match_info['name']
    async with request.app.proxy_client.post('http://socat:8080/images/create', params={'fromImage': name}) as response:
        while 1:
            line = await response.content.readline()
            if not line:
                break
            print(line)

    return web.Response(body=b'ok')


def main():
    loop = aio.get_event_loop()

    loop.add_signal_handler(signal.SIGTERM, terminate, loop)


    app = web.Application()
    app.router.add_route(
        'POST', '/image/{name}', create_image)

    app.proxy_client = aiohttp.ClientSession()

    handler = app.make_handler()
    srv = loop.run_until_complete(loop.create_server(handler, '0.0.0.0', 8080))

    loop.run_forever()

    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(app.shutdown())
    loop.run_until_complete(handler.finish_connections(5))
    loop.run_until_complete(app.cleanup())
    loop.close()

    loop.run_until_complete(proxy_client.close())

    loop.close()


if __name__ == '__main__':
    main()
