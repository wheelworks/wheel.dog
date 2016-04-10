import os
import signal
from functools import partial

import asyncio as aio
from aiohttp import web

import ibiza.watcher
import ibiza.coordinator.web


def terminate(watch_task):
    print('Terminating')

    watch_task.cancel()


async def watch():
    changed_generator = ibiza.watcher.get_changed_generator()

    while 1:
        paths = next(changed_generator)

        if paths:
            print('Files changed', paths)
            break

        try:
            await aio.sleep(1)
        except aio.CancelledError:
            break


def add_json_route(router, method, path, handler):
    async def wrapper(request):
        return web.json_response(await handler(request))

    return router.add_route(method, path, wrapper)


def main():
    loop = aio.get_event_loop()
    watch_task = aio.ensure_future(watch())
    loop.add_signal_handler(signal.SIGTERM, terminate, watch_task)

    app = web.Application()
    app.pending_queue = aio.Queue()
    app.router.add_json_route = partial(add_json_route, app.router)
    app.router.add_json_route(
        'GET', '/tasks/next', ibiza.coordinator.web.get_next_task)
    app.router.add_json_route(
        'POST', '/tasks', ibiza.coordinator.web.create_task)

    handler = app.make_handler()
    srv = loop.run_until_complete(loop.create_server(handler, '0.0.0.0', 8080))

    print('Started PID', os.getpid())

    loop.run_until_complete(watch_task)

    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(app.shutdown())
    loop.run_until_complete(handler.finish_connections(5))
    loop.run_until_complete(app.cleanup())
    loop.close()


if __name__ == '__main__':
    main()
