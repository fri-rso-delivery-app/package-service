from uuid import UUID
from pydantic import BaseModel


from ._common import CommonBase, CommonBaseRead


# common (base, read, write)
class TaskBase(BaseModel):
    title: str
    description: str


# db-only overrides
class Task(CommonBase, TaskBase):
    user_id: UUID


# create-only overrides
class TaskCreate(TaskBase):
    pass


# updatable fields
class TaskUpdate(BaseModel):
    description: str | None


# read-only overrides
class TaskRead(CommonBaseRead, TaskBase):
    pass
