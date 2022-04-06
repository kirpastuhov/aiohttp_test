from aiohttp import web
from main.models import Template, User, User_Workspace, User_Workspace_Template, Workspace, Workspace_Template
from main.views.workspace import link_templates
from psycopg2.errors import ForeignKeyViolation, UniqueViolation
from sqlalchemy import delete, insert, select, update


async def get_all_users(request: web.Request) -> web.json_response:
    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(select(User))
        data = await cursor.fetchall()
        users = [dict(q) for q in data]
        return web.json_response({"status": "ok", "data": users})


async def get_user_by_id(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]

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

    data = await request.json()
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
    data = await request.json()
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

    data = await request.json()
    name = data.get("name")
    workspace_type = data.get("type")
    template_types = data.get("template_types")

    if not name or not user_id or not workspace_type:
        return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Workspace).values(name=name))
            new_user_workspace = await cursor.fetchone()

            cursor = await conn.execute(
                insert(User_Workspace).values(user_id=user_id, workspace_id=new_user_workspace.id)
            )

            if template_types:
                response = await link_templates(conn, new_user_workspace.id, template_types)
                if response["status"] == "fail":
                    return web.json_response(response, status=400)

            cursor = await conn.execute(select(Template).where(Template.type.in_(template_types)))
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
            return web.json_response(
                {"status": "fail", "reason": "Workspace with such name already exists"}, status=400
            )
        except ForeignKeyViolation:
            cursor = await conn.execute(delete(Workspace).where(Workspace.name == name))
            return web.json_response({"status": "fail", "reason": "User with such id does not exist"}, status=400)


async def get_users_templates_for_workspace(request: web.Request) -> web.json_response:
    user_id = request.match_info["user_id"]
    workspace_id = request.match_info["workspace_id"]

    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(
            select(User_Workspace_Template).where(
                User_Workspace_Template.workspace_id == workspace_id, User_Workspace_Template.user_id == user_id
            )
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

    data = await request.json()
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
        if cursor.rowcount == 1:
            updated_template = await cursor.fetchone()
            return web.json_response({"status": "ok", "data": dict(updated_template)}, status=200)
        return web.json_response({"status": "fail", "reason": ""}, status=400)


async def delete_users_template(request: web.Request) -> web.json_response:
    user_id = int(request.match_info["user_id"])
    workspace_id = int(request.match_info["workspace_id"])
    template_id = int(request.match_info["template_id"])

    async with request.app["db"].acquire() as conn:
        cursor = await conn.execute(
            delete(User_Workspace_Template).where(
                User_Workspace_Template.user_id == user_id,
                User_Workspace_Template.workspace_id == workspace_id,
                User_Workspace_Template.template_id == template_id,
            )
        )
        if cursor.rowcount == 1:
            cursor = await conn.execute(delete(Workspace_Template).where(Workspace_Template.template_id == template_id))
            if cursor.rowcount == 1:
                cursor = await conn.execute(delete(Template).where(Template.id == template_id, Template.type == None))
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

    data = await request.json()
    config = data["config"]
    # template_type = data["type"]

    # if not template_type and not config:
    # return web.json_response({"status": "fail", "reason": "Some field is missing"}, status=400)

    async with request.app["db"].acquire() as conn:
        try:
            cursor = await conn.execute(insert(Template).values(config=config))
            new_user_template = await cursor.fetchone()
            cursor = await conn.execute(
                insert(User_Workspace_Template).values(
                    user_id=user_id, workspace_id=workspace_id, template_id=new_user_template.id, config=config
                )
            )
            cursor = await conn.execute(
                insert(Workspace_Template).values(workspace_id=workspace_id, template_id=new_user_template.id)
            )
            return web.json_response({"status": "ok", "data": dict(new_user_template)}, status=201)
        except UniqueViolation:
            return web.json_response({"status": "fail", "reason": "Template with such name already exists"}, status=400)
