from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from app.db import db
from app.models.tasks import *
from app.models.jwt import *
from app.auth import get_current_user


TABLE = 'tasks'
table = db[TABLE]


router = APIRouter(
    prefix='/tasks',
    tags=['tasks'],
)


async def get_task(
    id: str | UUID,
    # enforce ownership + auth
    token: JWTokenData = Depends(get_current_user),
) -> Task:
    task = await table.find_one({'_id': str(id), 'user_id': str(token.user_id)})
    if not task: raise HTTPException(status_code=404, detail=f'Task not found')

    return Task(**task)


@router.post('/', response_model=TaskRead)
async def create_task(*, task: TaskCreate, token: JWTokenData = Depends(get_current_user), ):
    # create
    task_db = jsonable_encoder(Task(**task.dict(), user_id=token.user_id))
    new_task = await table.insert_one(task_db)
    created_task = await get_task(new_task.inserted_id, token)
    
    return created_task


@router.get('/', response_model=List[TaskRead])
async def list_tasks(token: JWTokenData = Depends(get_current_user)):
    return await table.find({'user_id': str(token.user_id)}).to_list(1000)


@router.get('/{id}', response_model=TaskRead)
async def read_task(task: Task = Depends(get_task)):
    return task


@router.patch('/{id}', response_model=TaskRead)
async def update_task(*,
    token: JWTokenData = Depends(get_current_user),
    task: Task = Depends(get_task),
    task_update: TaskUpdate
):
    # update task
    task_update = task_update.dict(exclude_unset=True)
    await table.update_one({'_id': str(task.id)}, {'$set': task_update})
    
    return await get_task(task.id, token)


@router.delete('/{id}')
async def delete_task(task: Task = Depends(get_task),):
    await table.delete_one({'_id': str(task.id)})

    return { 'ok': True }
