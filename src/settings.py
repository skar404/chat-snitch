from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    api_id: str
    api_hash: str

    is_memory: bool = True

    role_message = (
        "Hi! We have some roles:"
        "\n-role 1"
        "\n-role 2"
    )

    class Config:
        env_file = '.env', '../.env'


settings = Settings()
