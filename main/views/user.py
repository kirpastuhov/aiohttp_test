from aiohttp import web
from main.models import Template, User, User_Workspace, User_Workspace_Template, Workspace, Workspace_Template
from main.views.utils import vaildate_body
from psycopg2.errors import UniqueViolation
from sqlalchemy import delete, insert, select, update


async def get_all_users(request: web.Request) -> web.json_response:
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(User))
        data = await cursor.fetchall()
        users = [dict(q) for q in data]
        return web.json_response({"status": "ok", "data": users})


async def get_user_by_id(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]

    if not user_id.isdigit():
        return web.json_response({"status": "fail", "reason": "User id should be an int"}, status=400)

    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(User).where(User.id == user_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": f"User {user_id} doesn't exist"},
                status=404,
            )
        record = await cursor.fetchone()
    return web.json_response({"status": "ok", "data": dict(record)})


async def update_user_by_id(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]

    if not user_id.isdigit():
        return web.json_response({"status": "fail", "reason": "User id should be an int"}, status=400)

    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    name = data.get("name")

    if not name:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            await conn.execute(update(User).where(User.id == user_id).values(name=name))
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "User with such name already exists"}, status=400)
        cursor = await conn.execute(select(User).where(User.id == user_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": f"User with id {user_id} doesn't exist"},
                status=404,
            )
        updated_user = await cursor.fetchone()
        return web.json_response({"status": "ok", "data": dict(updated_user)}, status=200)


async def delete_user_by_id(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(delete(User).where(User.id == user_id))
        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"User {user_id} doesn't exist"}, status=404)


async def create_user(request: web.Request) -> web.json_response:
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)

    name = data.get("name")
    if not name:
        return web.json_response({"status": "fail", "reason": "Name can't be empty"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(User).values(name=name))
            new_workspace = await cursor.fetchone()
            return web.json_response({"status": "ok", "data": dict(new_workspace)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "User with such name already exists"}, status=400)


async def get_users_workspaces(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(Workspace).join(User_Workspace).where(User_Workspace.user_id == user_id))
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": "User doesn't have any workspaces yet"},
                status=404,
            )
        data = await cursor.fetchall()
        user_workspaces = [dict(q) for q in data]
    return web.json_response({"status": "okkkk", "data": user_workspaces})


async def create_user_workspace(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    name = data.get("name")
    workspace_type = data.get("type")

    if not name or not user_id or not workspace_type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Workspace).values(name=name))
            new_user_workspace = await cursor.fetchone()

            cursor = await conn.execute(insert(User_Workspace).values(user_id=user_id, workspace_id=new_user_workspace.id))

            cursor = await conn.execute(select(Workspace_Template).join(Workspace).where(Workspace.type == workspace_type))
            all_templates = await cursor.fetchall()

            template_ids = [x.template_id for x in all_templates]

            cursor = await conn.execute(select(Template).where(Template.id.in_(template_ids)))
            data = await cursor.fetchall()
            for template in data:
                cursor = await conn.execute(
                    insert(User_Workspace_Template).values(
                        user_id=user_id,
                        workspace_id=new_user_workspace.id,
                        template_id=template.id,
                        config=template.config,
                    )
                )

            return web.json_response({"status": "ok", "data": dict(new_user_workspace)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "Workspace with such name already exists"}, status=400)


async def get_users_templates_for_workspace(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    workspace_id = request.match_info["workspace_id"]
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(
            select(User_Workspace_Template).where(User_Workspace_Template.workspace_id == workspace_id, User_Workspace_Template.user_id == user_id)
        )
        if cursor.rowcount == 0:
            return web.json_response(
                {"status": "fail", "reason": "User doesn't have any templates yet"},
                status=404,
            )
        data = await cursor.fetchall()
        user_templates = [dict(q) for q in data]
    return web.json_response({"status": "ok", "data": user_templates})


async def patch_users_template(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    workspace_id = request.match_info["workspace_id"]
    template_id = request.match_info["template_id"]

    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    config = data.get("config")

    if not config:
        return web.json_response({"status": "fail", "reason": "Config field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        await conn.execute(
            update(User_Workspace_Template)
            .where(
                User_Workspace_Template.user_id == user_id,
                User_Workspace_Template.template_id == template_id,
                User_Workspace_Template.workspace_id == workspace_id,
            )
            .values(config=config)
        )
        cursor = await conn.execute(
            select(User_Workspace_Template).where(
                User_Workspace_Template.user_id == user_id,
                User_Workspace_Template.template_id == template_id,
                User_Workspace_Template.workspace_id == workspace_id,
            )
        )
        updated_template = await cursor.fetchone()
        return web.json_response({"status": "ok", "data": dict(updated_template)}, status=200)


async def delete_users_template(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    workspace_id = request.match_info["workspace_id"]
    template_id = request.match_info["template_id"]

    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(
            delete(User_Workspace_Template).where(
                User_Workspace_Template.template_id == template_id,
                User_Workspace_Template.user_id == user_id,
                User_Workspace_Template.workspace_id == workspace_id,
            )
        )
        cursor = await conn.execute(delete(Template).where(Template.id == int(template_id)))
        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"Template {template_id} doesn't exist"}, status=404)


async def delete_users_workspace(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    workspace_id = request.match_info["workspace_id"]

    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(User_Workspace))
        all_workspaces = await cursor.fetchall()
        all_workspaces = [dict(q) for q in all_workspaces]

        user_workspaces = [x.get("workspace_id") for x in all_workspaces if x.get("user_id") == int(user_id)]

        if int(workspace_id) not in user_workspaces:
            return web.json_response(
                {"status": "fail", "reason": f"Workspace {workspace_id} doesn't does not belong to user {user_id}"},
                status=400,
            )

        cursor = await conn.execute(delete(Workspace).where(Workspace.id == workspace_id))

        if cursor.rowcount == 1:
            return web.json_response({"status": "ok", "data": []}, status=200)
        return web.json_response({"status": "fail", "reason": f"Workspace {workspace_id} doesn't exist"}, status=404)


async def create_user_template(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    workspace_id = request.match_info["workspace_id"]
    data = await vaildate_body(request)
    if not data or isinstance(data, list):
        return web.json_response({"status": "fail", "reason": "Invalid body"}, status=400)
    config = data["config"]
    template_name = data["name"]

    if not template_name and not config:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Template).values(name=template_name, config=config))
            new_user_template = await cursor.fetchone()
            cursor = await conn.execute(
                insert(User_Workspace_Template).values(user_id=user_id, workspace_id=workspace_id, template_id=new_user_template.id, config=config)
            )
            return web.json_response({"status": "ok", "data": dict(new_user_template)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "Template with such name already exists"}, status=400)
