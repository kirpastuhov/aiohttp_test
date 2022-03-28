from aiohttp import web
from main.models import Workspace, Workspace_Template
from main.views.utils import vaildate_body
from psycopg2.errors import UniqueViolation
from sqlalchemy import delete, insert, select, update


async def get_all_workspaces(request: web.Request) -> web.json_response:
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(Workspace))
        data = await cursor.fetchall()
        workspaces = [dict(q) for q in data]
    return web.json_response({"status": "ok", "data": workspaces})


async def get_workspace_by_id(request: web.Request) -> web.json_response:
    workspace_id = request.match_info["workspace_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(Workspace).where(Workspace.id == workspace_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": f"Workspace {workspace_id} doesn't exist"},
                status=404,
            )
        record = await cursor.fetchone()
    return web.json_response({"status": "ok", "data": dict(record)})


async def create_workspace(request: web.Request) -> web.json_response:
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    name = data.get("name")
    type = data.get("type")
    if not name or not type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Workspace).values(name=name, type=type))

            new_workspace = await cursor.fetchone()

            return web.json_response({"status": "ok", "data": dict(new_workspace)}, status=201)
        except UniqueViolation:
            return web.json_response(
                {"status": "fail", "reason": "Workspace with such name already exists"}, status=400
            )


async def update_workspace_by_id(request: web.Request) -> web.json_response:
    workspace_id = request.match_info["workspace_id"]

    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)

    name = data.get("name")
    type = data.get("type")
    if not name or not type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        await conn.execute(update(Workspace).where(Workspace.id == workspace_id).values(name=name, type=type))
        cursor = await conn.execute(select(Workspace).where(Workspace.id == workspace_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": f"Workspace {workspace_id} doesn't exist"},
                status=404,
            )

        updated_workspace = await cursor.fetchone()
        return web.json_response({"status": "ok", "data": dict(updated_workspace)}, status=200)


async def delete_workspace_by_id(request: web.Request) -> web.json_response:
    workspace_id = request.match_info["workspace_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(delete(Workspace).where(Workspace.id == workspace_id))
        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"Workspace {workspace_id} doesn't exist"}, status=404)


async def link_template(request: web.Request) -> web.json_response:
    # TODO: Prevent duplicates in Workspace_Template table
    workspace_id = request.match_info["workspace_id"]
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    template_id = data.get("template_id")

    if not template_id:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(
            insert(Workspace_Template).values(template_id=template_id, workspace_id=workspace_id)
        )
        new_workspace = await cursor.fetchone()
        return web.json_response({"status": "ok", "data": dict(new_workspace)})
