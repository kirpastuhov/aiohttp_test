from main.views.template import (
    create_template,
    delete_template_by_id,
    get_all_templates,
    get_template_by_id,
    update_template_by_id,
)
from main.views.user import (
    create_new_user_workspace,
    create_user,
    delete_users_template,
    delete_users_workspace,
    get_all_users,
    get_user_by_id,
    get_users_templates_for_workspace,
    get_users_workspaces,
    patch_users_template,
)
from main.views.workspace import (
    create_workspace,
    delete_workspace_by_id,
    get_all_workspaces,
    get_workspace_by_id,
    link_template,
    update_workspace_by_id,
)


def setup_routes(app):

    app.router.add_get("/template", get_all_templates, name="get_all_templates")
    app.router.add_get("/template/{template_id}", get_template_by_id, name="get_template_by_id")
    app.router.add_post("/template", create_template, name="create_template")
    app.router.add_patch("/template/{template_id}", update_template_by_id, name="update_template_by_id")
    app.router.add_delete("/template/{template_id}", delete_template_by_id, name="delete_template_by_id")

    app.router.add_get("/workspace", get_all_workspaces, name="get_all_workspaces")
    app.router.add_get("/workspace/{workspace_id}", get_workspace_by_id, name="get_workspace_by_id")
    app.router.add_post("/workspace", create_workspace, name="post_workspace")
    app.router.add_patch("/workspace/{workspace_id}", update_workspace_by_id, name="update_workspace_by_id")
    app.router.add_delete("/workspace/{workspace_id}", delete_workspace_by_id, name="delete_workspace_by_id")

    app.router.add_post("/workspace/{workspace_id}/link_template", link_template, name="link_workspace")

    app.router.add_get("/user", get_all_users, name="get_all_users")
    app.router.add_get("/user/{user_id}", get_user_by_id, name="get_user_by_id")
    app.router.add_post("/user", create_user, name="create_user")

    app.router.add_get("/user/{user_id}/workspace", get_users_workspaces, name="get_users_workspaces")
    app.router.add_get(
        "/user/{user_id}/workspace/{workspace_id}/template",
        get_users_templates_for_workspace,
        name="get_users_templates_for_workspace",
    )
    app.router.add_patch(
        "/user/{user_id}/workspace/{workspace_id}/template/{template_id}",
        patch_users_template,
        name="get_users_template_by_id_for_workspace",
    )
    app.router.add_delete(
        "/user/{user_id}/workspace/{workspace_id}/template/{template_id}",
        delete_users_template,
        name="delete_users_template",
    )

    app.router.add_delete(
        "/user/{user_id}/workspace/{workspace_id}",
        delete_users_workspace,
        name="delete_users_workspace",
    )

    app.router.add_post("/user/{user_id}/workspace", create_new_user_workspace, name="user_new_workspace")
