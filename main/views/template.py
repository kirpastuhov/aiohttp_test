from aiohttp import web
from main.models import Template, Workspace_Template
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
                {"status": "fail", "reason": f"Template {template_id} doesn't exist"},
                status=404,
            )
        record = await cursor.fetchone()
    return web.json_response({"status": "ok", "data": dict(record)})


async def create_template(request: web.Request) -> web.json_response:
    data = await request.json()

    config = data.get("config")
    template_type = data.get("type")
    if not config or not template_type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Template).values(config=config, type=template_type))
            new_template = await cursor.fetchone()
            return web.json_response({"status": "ok", "data": dict(new_template)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "Template with such type already exists"}, status=400)


async def update_template_by_id(request: web.Request) -> web.json_response:
    template_id = request.match_info["template_id"]
    data = await request.json()

    template_type = data.get("type")
    config = data.get("config")

    if not template_type or not config:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            await conn.execute(update(Template).where(Template.id == template_id).values(type=template_type, config=config))
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": f"Template with type '{template_type}' already exists"}, status=400)

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
        cursor = await conn.execute(delete(Workspace_Template).where(Workspace_Template.template_id == template_id))
        cursor = await conn.execute(delete(Template).where(Template.id == template_id))
        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"Template {template_id} doesn't exist"}, status=404)
