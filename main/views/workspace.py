from aiohttp import web
import aiopg
from main.models import Workspace, Workspace_Template, Template
from main.views.utils import vaildate_body
from psycopg2.errors import UniqueViolation, ForeignKeyViolation
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
    data = await request.json()

    name = data.get("name")
    workspace_type = data.get("type")
    template_types = data.get("template_types")
    if not name or not workspace_type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Workspace).values(name=name, type=workspace_type))
            new_workspace = await cursor.fetchone()

            if template_types:
                response = await link_templates(conn, new_workspace.id, template_types)
                if response["status"] == "fail":
                    return web.json_response(response, status=400)

            return web.json_response({"status": "ok", "data": dict(new_workspace)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "Workspace with such name already exists"}, status=400)


async def update_workspace_by_id(request: web.Request) -> web.json_response:
    # TODO: Remove workspace type field?
    workspace_id = request.match_info["workspace_id"]
    data = await request.json()

    name = data.get("name")
    workspace_type = data.get("type")
    if not name or not workspace_type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        await conn.execute(update(Workspace).where(Workspace.id == workspace_id).values(name=name, type=workspace_type))
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
        cursor = await conn.execute(delete(Workspace_Template).where(Workspace_Template.workspace_id == workspace_id))
        cursor = await conn.execute(delete(Workspace).where(Workspace.id == workspace_id))
        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"Workspace {workspace_id} doesn't exist"}, status=404)


async def link_templates(conn: aiopg.connection, workspace_id: int, template_types: list) -> dict:
    try:
        for template_type in template_types:
            cursor = await conn.execute(select(Template).where(Template.type == template_type))
            template = await cursor.fetchone()
            cursor = await conn.execute(insert(Workspace_Template).values(template_id=template.id, workspace_id=workspace_id))
        return {"status": "ok"}
    except ForeignKeyViolation:
        return {"status": "fail", "reason": f"Template {template.id} doesn't exist"}
    except UniqueViolation:
        return {"status": "fail", "reason": f"Template {template.id} is already linked to workspace {workspace_id}"}


async def link_template(request: web.Request) -> web.json_response:
    workspace_id = request.match_info["workspace_id"]
    data = await request.json()

    template_id = data.get("template_id")
    if not template_id:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Workspace_Template).values(template_id=template_id, workspace_id=workspace_id))
            cursor = await conn.execute(
                select(Workspace_Template).where(Workspace_Template.template_id == template_id, Workspace_Template.workspace_id == workspace_id)
            )
            new_workspace = await cursor.fetchone()
            return web.json_response({"status": "ok", "data": dict(new_workspace)})
        except ForeignKeyViolation:
            return web.json_response(
                {"status": "fail", "reason": f"Template {template_id} doesn't exist"},
                status=404,
            )
        except UniqueViolation:
            return web.json_response(
                {"status": "fail", "reason": f"Template {template_id} is already linked to workspace {workspace_id}"},
                status=404,
            )
