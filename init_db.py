from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from main.models import Base, Template, User, Workspace, Workspace_Template


def create_tables(engine):
    Base.metadata.create_all(engine)
    print("Created all tables")


def drop_tables(engine):
    Base.metadata.drop_all(engine)
    print("Dropped all tables")


def sample_data(engine):
    with Session(engine) as session:
        workspace_1 = Workspace(name="Office workspace", type="OW")
        workspace_2 = Workspace(name="Home workspace", type="HW")

        template_1 = Template(config=[{"key": "value"}], type="Office")
        template_2 = Template(config=[{"another_key": "different_value"}], type="Home")

        usr_1 = User(name="John")
        usr_2 = User(name="Alex")

        # workspace_template_1 = Workspace_Template(workspace_id=1, template_id=1)
        # workspace_template_2 = Workspace_Template(workspace_id=2, template_id=2)

        # session.add_all([workspace_1, workspace_2, template_1, template_2, usr_1, usr_2, workspace_template_1, workspace_template_2])
        session.add_all([workspace_1, workspace_2, template_1, template_2, usr_1, usr_2])
        session.commit()


async def init_database():
    ADMIN_DB_URL = "postgresql://postgres:password@postgres_db:5432/postgres"

    admin_engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")

    drop_tables(engine=admin_engine)
    create_tables(engine=admin_engine)
    sample_data(engine=admin_engine)


if __name__ == "__main__":
    init_database()
