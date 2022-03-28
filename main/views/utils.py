from json.decoder import JSONDecodeError

from aiohttp import web


async def vaildate_body(request: web.Request):
    try:
        data = await request.json()
        return data
    except JSONDecodeError:
        return
