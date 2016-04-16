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

    task = aio.Task.current_task()

    def done_callback(_):
        for worklet_task in worklets:
            worklet_task.cancel()

    task.add_done_callback(done_callback)

    def worklet_done(future):
        worklets.remove(future)
        semaphore.release()

    while 1:
        if semaphore.locked():
            print('We are full')

        await semaphore.acquire()
        semaphore.release()

        try:
            print('Waiting for a next task')
            async with coordinator.get('http://coordinator:8080/tasks/next') as response:
                sleep = int((await response.json())['sleep'])
            print('Got task')
        except aiohttp.ClientConnectionError:
            print('Coordinator connection error, retrying in 3 seconds')
            await aio.sleep(3)
            continue
        except aiohttp.ClientResponseError:
            print('Coordinator disconnected')
            continue

        # this cannot block
        await semaphore.acquire()
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

    try:
        loop.run_until_complete(aio.gather(work_task, watch_task))
    except aio.CancelledError:
        pass

    loop.run_until_complete(coordinator.close())

    loop.close()


if __name__ == '__main__':
    main()
