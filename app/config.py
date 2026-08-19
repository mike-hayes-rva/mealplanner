from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    minio_endpoint: str
    minio_root_user: str
    minio_root_password: str
    minio_bucket: str = "recipe-images"
    minio_use_ssl: bool = False


settings = Settings()
