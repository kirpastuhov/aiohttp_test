from aiohttp import web
from json import JSONDecodeError


@web.middleware
async def validate_id_middleware(request: web.Request, handler: web.Request):
    try:
        if "/template/" in request.raw_path:
            item_id = request.match_info["template_id"]
            if not item_id.isdigit():
                return web.json_response({"status": "fail", "reason": "Template id should be an int!"}, status=400)
        elif "/workspace/" in request.raw_path:
            item_id = request.match_info["workspace_id"]
            if not item_id.isdigit():
                return web.json_response({"status": "fail", "reason": "Workspace id should be an int!"}, status=400)
        elif "/user/" in request.raw_path:
            item_id = request.match_info["user_id"]
            if not item_id.isdigit():
                return web.json_response({"status": "fail", "reason": "User id should be an int!"}, status=400)
    except KeyError:
        return web.json_response({"status": "Trailing slash. Remove it and try again"})
    resp = await handler(request)
    return resp


@web.middleware
async def validate_json_body_middleware(request: web.Request, handler: web.Request):
    if request.method in ["POST", "PATCH"]:
        try:
            data = await request.json()
            if not data or isinstance(data, list):
                return web.json_response({"status": "fail", "reason": "Invalid body!"}, status=400)
        except JSONDecodeError:
            return web.json_response({"status": "fail", "reason": "Invalid json body!"}, status=400)
    resp = await handler(request)
    return resp
