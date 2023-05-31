from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    api_id: str
    api_hash: str

    is_memory: bool = True

    redis_host: str = 'localhost'
    redis_port: int = 6370
    redis_db: int = 0

    role_message = (
        "Hi, is a base chat role.\n"
        "You need use command /set_role to change it.\n"
    )

    class Config:
        env_file = '.env', '../.env'


settings = Settings()
