from json.decoder import JSONDecodeError

from aiohttp import web
from main.models import Template
from main.views.utils import vaildate_body
from psycopg2.errors import UniqueViolation
from sqlalchemy import delete, insert, select, update


async def get_all_templates(request: web.Request) -> web.json_response:
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(Template))
        data = await cursor.fetchall()
        templates = [dict(q) for q in data]
        return web.json_response({"status": "ok", "data": templates})


async def get_template_by_id(request: web.Request) -> web.json_response:
    template_id = request.match_info["template_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(Template).where(Template.id == template_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": f"Workspace {template_id} doesn't exist"},
                status=404,
            )
        record = await cursor.fetchone()
    return web.json_response({"status": "ok", "data": dict(record)})


async def create_template(request: web.Request) -> web.json_response:
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)

    name = data.get("name")
    config = data.get("config")
    if not name or not config:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Template).values(name=name, config=config))
            new_template = await cursor.fetchone()
            return web.json_response({"status": "ok", "data": dict(new_template)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "Template with such name already exists"}, status=400)


async def update_template_by_id(request: web.Request) -> web.json_response:
    template_id = request.match_info["template_id"]
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    name = data.get("name")
    config = data.get("config")

    if not name or not config:
        return web.json_response({"status": "fail", "reason": f"Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        await conn.execute(update(Template).where(Template.id == template_id).values(name=name, config=config))
        cursor = await conn.execute(select(Template).where(Template.id == template_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": f"Template {template_id} doesn't exist"},
                status=404,
            )
        updated_template = await cursor.fetchone()
        return web.json_response({"status": "ok", "data": dict(updated_template)}, status=200)


async def delete_template_by_id(request: web.Request) -> web.json_response:
    template_id = request.match_info["template_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(delete(Template).where(Template.id == template_id))
        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"Template {template_id} doesn't exist"}, status=404)
