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
        "Hi! We have some roles:"
        "\n-role 1"
        "\n-role 2"
    )

    class Config:
        env_file = '.env', '../.env'


settings = Settings()
