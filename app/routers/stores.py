from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from app.db import db
from app.models.stores import *
from app.models.jwt import *
from app.auth import get_current_user


TABLE = 'stores'
table = db[TABLE]


router = APIRouter(
    prefix='/stores',
    tags=['stores'],
)


async def get_store(
    id: str | UUID,
    # enforce ownership + auth
    token: JWTokenData = Depends(get_current_user),
) -> Store:
    store = await table.find_one({'_id': str(id), 'user_id': str(token.user_id)})
    if not store: raise HTTPException(status_code=404, detail=f'Store not found')

    return Store(**store)


@router.post('/', response_model=StoreRead)
async def create_store(*, store: StoreCreate, token: JWTokenData = Depends(get_current_user), ):
    # create
    store_db = jsonable_encoder(Store(**store.dict(), user_id=token.user_id))
    new_store = await table.insert_one(store_db)
    created_store = await get_store(new_store.inserted_id, token)
    
    return created_store


@router.get('/', response_model=List[StoreRead])
async def list_stores(token: JWTokenData = Depends(get_current_user)):
    return await table.find({'user_id': str(token.user_id)}).to_list(1000)


@router.get('/{id}', response_model=StoreRead)
async def read_store(store: Store = Depends(get_store)):
    return store


@router.patch('/{id}', response_model=StoreRead)
async def update_store(*,
    token: JWTokenData = Depends(get_current_user),
    store: Store = Depends(get_store),
    store_update: StoreUpdate
):
    # update store
    store_update = store_update.dict(exclude_unset=True)
    await table.update_one({'_id': str(store.id)}, {'$set': store_update})
    
    return await get_store(store.id, token)


@router.delete('/{id}')
async def delete_store(store: Store = Depends(get_store),):
    await table.delete_one({'_id': str(store.id)})

    return {'ok': True}
