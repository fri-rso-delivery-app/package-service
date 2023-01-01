from uuid import UUID
from pydantic import BaseModel


from ._common import CommonBase, CommonBaseRead


# common (base, read, write)
class StoreBase(BaseModel):
    store_id: UUID
    location: str


# db-only overrides
class Store(CommonBase, StoreBase):
    pass


# create-only overrides
class StoreCreate(StoreBase):
    pass


# updatable fields
class StoreUpdate(BaseModel):
    pass


# read-only overrides
class StoreRead(CommonBaseRead, StoreBase):
    pass
