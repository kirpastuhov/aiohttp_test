import aiopg.sa
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from sqlalchemy_json import mutable_json_type

Base = declarative_base()
meta = MetaData()


class Workspace_Template(Base):
    __tablename__ = "workspace_template"
    workspace_id = Column(Integer, ForeignKey("workspace.id"), primary_key=True)
    template_id = Column(Integer, ForeignKey("template.id"), primary_key=True)

    workspace = relationship("Workspace", backref=backref("workspace_template", cascade="all, delete-orphan"))
    template = relationship("Template", backref=backref("workspace_template", cascade="all, delete-orphan"))

    def __init__(self, workspace_id=None, template_id=None):
        self.workspace_id = workspace_id
        self.template_id = template_id

    def __repr__(self):
        return f"<Workspace_Template {self.workspace.name} {self.template.name}>"


class User_Workspace(Base):
    __tablename__ = "user_workspace"
    id = Column(Integer, autoincrement=True, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspace.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    workspaces = relationship("Workspace", backref=backref("user_workspace", cascade="all, delete-orphan"))
    users = relationship("User", backref=backref("user_workspace", cascade="all, delete-orphan"))

    def __init__(self, workspace_id=None, user_id=None):
        self.workspace_id = workspace_id
        self.user_id = user_id


class User_Workspace_Template(Base):
    __tablename__ = "user_workspace_template"
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspace.id", ondelete="CASCADE"), primary_key=True)
    template_id = Column(Integer, ForeignKey("template.id"), primary_key=True)
    config = Column(mutable_json_type(dbtype=JSONB, nested=True))

    def __init__(self, user_id=None, workspace_id=None, template_id=None):
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.template_id = template_id


class Template(Base):
    __tablename__ = "template"
    id = Column(Integer, primary_key=True)
    config = Column(mutable_json_type(dbtype=JSONB, nested=True))
    type = Column(String(250), nullable=False, unique=True)

    workspaces = relationship("Workspace", secondary="workspace_template", viewonly=True)

    def __init__(self, config=None, type=None):
        self.config = config
        self.type = type

    def __repr__(self) -> str:
        return f"<Template {self.name}>"


class Workspace(Base):
    __tablename__ = "workspace"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(100), nullable=True)

    templates = relationship("Template", secondary="workspace_template", viewonly=True)

    def __init__(self, name=None, type=None):
        self.name = name
        self.type = type

    def __repr__(self) -> str:
        return f"<Workspace {self.name}>"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    workspaces = relationship("Workspace", secondary="user_workspace", viewonly=True)

    def __init__(self, name=None):
        self.name = name

    def __repr__(self) -> str:
        return f"<User {self.name}>"


async def pg_context(app):
    conf = app["config"]["postgres"]
    engine = await aiopg.sa.create_engine(
        database=conf["database"],
        user=conf["user"],
        password=conf["password"],
        host=conf["host"],
        port=conf["port"],
    )
    app["db"] = engine

    yield

    app["db"].close()
    await app["db"].wait_closed()
