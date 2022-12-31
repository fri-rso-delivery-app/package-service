from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_title: str = 'packet microservice'
    app_name: str = 'packet'

    api_root_path: str = ''
    api_http_port: int = 8003
    api_db_url: str = 'mongodb://root:example@localhost:27017/'
    api_db_name: str = 'packet_service'

    # trace
    api_trace_url: str = 'http://localhost:4317'

    # other services
    auth_server: str = 'http://app-auth:8080'

    # auth settings
    api_login_url: str = 'http://localhost:8001/jwt/token'
    # to get a viable secret run:
    # openssl rand -hex 32
    api_secret_key: str = 'SECRET_REPLACE_ME'
    api_jwt_algorithm: str = 'HS256'

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
