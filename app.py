from aiohttp import web

from init_db import init_database
from main.models import pg_context
from main.routes import setup_routes


async def init_app() -> web.Application:
    print("Init APP")
    router = web.RouteTableDef()
    app = web.Application()
    app.add_routes(router)
    await init_database()

    setup_routes(app)

    app["config"] = {
        "postgres": {
            "database": "postgres",
            "user": "postgres",
            "password": "password",
            "host": "postgres_db",
            "port": "5432",
        }
    }

    app.cleanup_ctx.append(pg_context)

    return app


if __name__ == "__main__":
    web.run_app(init_app())
