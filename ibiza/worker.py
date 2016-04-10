from functools import partial
import signal
import os
import random

import asyncio as aio
import aiohttp

import ibiza.watcher


async def worklet(sleep):
    print('Started worklet', sleep)
    await aio.sleep(sleep)
    print('Ended worklet', sleep)


async def work(coordinator):
    semaphore = aio.BoundedSemaphore(4)
    worklets = []

    def worklet_done(future):
        worklets.remove(future)
        semaphore.release()

    while 1:
        if semaphore.locked():
            print('We are full')

        try:
            await semaphore.acquire()
        except aio.CancelledError:
            for worklet_task in worklets:
                worklet_task.cancel()
            break

        try:
            async with coordinator.get('http://localhost:8080/tasks/next') as response:
                sleep = int((await response.json())['sleep'])
        except aio.CancelledError:
            for worklet_task in worklets:
                worklet_task.cancel()
            break

        worklet_task = aio.ensure_future(worklet(sleep))

        worklet_task.add_done_callback(worklet_done)
        worklets.append(worklet_task)


async def watch(work_task):
    changed_generator = ibiza.watcher.get_changed_generator()

    while 1:
        paths = next(changed_generator)

        if paths:
            print('Files changed', paths)
            work_task.cancel()
            break

        await aio.sleep(1)


def terminate(tasks):
    print('Terminating')

    for task in tasks:
        task.cancel()


def main():
    loop = aio.get_event_loop()
    coordinator = aiohttp.ClientSession()

    work_task = aio.ensure_future(work(coordinator))
    watch_task = aio.ensure_future(watch(work_task))

    loop.add_signal_handler(signal.SIGTERM, terminate, [work_task, watch_task])

    print('Started PID', os.getpid())

    loop.run_until_complete(aio.wait([work_task, watch_task]))

    loop.run_until_complete(coordinator.close())

    loop.close()


if __name__ == '__main__':
    main()
