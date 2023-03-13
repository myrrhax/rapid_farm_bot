from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    bot_token: SecretStr
    admin_link_payload: SecretStr
    postgres_db: SecretStr
    postgres_user: SecretStr
    host: SecretStr
    postgres_password: SecretStr
    socket_uri: SecretStr

    class Config:
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"

config = Settings()