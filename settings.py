import pydantic


class Settings(pydantic.BaseSettings):
    smsc_login: str
    smsc_password: str
    phone_numbers: str
    valid: int = 1
    mock_return_value: bool = True

    redis_uri: str

    class Config:
        env_file = ".env"


settings = Settings()
