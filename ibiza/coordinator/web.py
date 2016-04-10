async def get_next_task(request):
    return await request.app.pending_queue.get()


async def create_task(request):
    request.app.pending_queue.put_nowait(await request.json())

    return {}
