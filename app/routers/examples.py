import logging
from fastapi import APIRouter, Depends, Header

from app.models.jwt import *
from app.models.users import *
from app.auth import get_current_user, get_current_user_data


router = APIRouter(
    prefix='/examples',
    tags=['examples'],
)


@router.get('/warning')
async def list_tasks():
    logging.warning('This is an example warning log')
    return 'warning logged'


@router.get('/error')
async def list_tasks():
    logging.error('This is an example error log')
    return 'error logged'


@router.get('/exception')
async def list_tasks():
    raise Exception('Intentional exception')

    return 'Exception raised' # unreachable code


@router.get('/user_data', response_model=UserRead)
async def list_tasks(
    token: JWTokenData = Depends(get_current_user),
    user_data: UserRead = Depends(get_current_user_data)
):
    logging.info('Retreiving user data from the auth server.')

    return user_data
