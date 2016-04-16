import asyncio as aio
import signal
import sys
import os


def reload(run_task):
    print('Reloading child')

    run_task.canceler = reload
    run_task.cancel()

def terminate(run_task):
    print('Terminating supervisor')
    run_task.canceler = terminate
    run_task.cancel()


def signal_child_reloading(child_reloading):
    print('Child will be terminating to reload')
    child_reloading.set()


async def run(child_reloading):
    while 1:
        child = await aio.create_subprocess_exec(sys.executable, *sys.argv[1:])

        print('Started child', child.pid)

        try:
            retcode = await child.wait()

            if child_reloading.is_set():
                print('Child exited for reloading')
                child_reloading.clear()
            else:
                print('Child unexpectadly exited with', retcode)
        except aio.CancelledError:
            print('Sending TERM to child')
            child.terminate()
            retcode = await child.wait()
            print('Child exited with', retcode)

            canceler = aio.Task.current_task().canceler

            assert(canceler in [reload, terminate])

            if canceler == terminate:
                break


def main():
    loop = aio.get_event_loop()
    child_reloading = aio.Event()
    run_task = aio.ensure_future(run(child_reloading))

    loop.add_signal_handler(signal.SIGTERM, terminate, run_task)
    loop.add_signal_handler(signal.SIGHUP, reload, run_task)
    loop.add_signal_handler(signal.SIGUSR1, signal_child_reloading, child_reloading)

    print('Started supervisor', os.getpid())

    loop.run_until_complete(run_task)

    loop.close()

if __name__ == '__main__':
    main()
