from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from app.models.jwt import *
from app.models.users import *
from app.config import Settings, get_settings


# auth scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=get_settings().api_login_url)

# generate exteption to re-use
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
):
    # verify user credentials
    try:
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.api_jwt_algorithm])
        username: str = payload.get('sub')
        user_id: str = payload.get('user_id')
        if username is None or user_id is None:
            raise credentials_exception
        
        return JWTokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # finally (this part of the code should be unreachable)
    raise credentials_exception


import httpx
from opentelemetry.propagate import inject


# get user data from the suth server
async def get_current_user_data(
    # ensure authorised
    token: JWTokenData = Depends(get_current_user),
    # to forward token
    authorization: str | None = Header(default=None, include_in_schema=False),
    # site settings
    settings: Settings = Depends(get_settings),
) -> UserRead:
    # create headers
    headers = {'Authorization': authorization}

    # inject trace info to header
    inject(headers)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{settings.auth_server}/users/my_profile',
            headers=headers,
        )

        if response.status_code == 200:
            user_data_str = response.read()
            return UserRead.parse_raw(user_data_str)
        if response.status_code == 401:
            raise credentials_exception
    
    raise Exception('Error while communicating with the auth server.')
