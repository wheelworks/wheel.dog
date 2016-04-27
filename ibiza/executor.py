import asyncio as aio
import os
import pprint
import sys

import aiohttp


async def query_containers(proxy_client):
    async with proxy_client.get('http://socat:8080/containers/json') as response:
        pprint.pprint(await response.json())


def main():
    loop = aio.get_event_loop()

    proxy_client = aiohttp.ClientSession()

    loop.run_until_complete(query_containers(proxy_client))
    loop.run_until_complete(proxy_client.close())

    loop.close()


if __name__ == '__main__':
    main()
