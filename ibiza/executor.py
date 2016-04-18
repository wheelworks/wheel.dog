import os
import asyncio as aio
import pprint

import aiohttp


async def start_socat():
    return await aio.create_subprocess_exec(
        'socat', '-d', '-d', 'TCP-LISTEN:8080,fork', 'UNIX:/var/run/docker.sock')


def drop_privileges():
    os.setgroups([])

    os.setegid(10000)
    os.seteuid(10000)


async def query_containers(proxy):
    async with proxy.get('http://localhost:8080/containers/json') as response:
        pprint.pprint(await response.json())


def main():
    loop = aio.get_event_loop()

    proxy = aiohttp.ClientSession()

    socat = loop.run_until_complete(start_socat())
    print('Started TCP to UNIX socket proxy')

    drop_privileges()
    print('Dropped root privileges')

    loop.run_until_complete(query_containers(proxy))

    loop.run_until_complete(proxy.close())

    print('Gained root priviledges')

    socat.terminate()
    loop.run_until_complete(socat.wait())

    loop.close()


if __name__ == '__main__':
    main()
