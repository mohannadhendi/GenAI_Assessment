from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):

    # Application settings
    APP_NAME: str 
    APP_VERSION: str 
    
    OPENAI_API_KEY: str
   
    POSTGRES_DB_URL: str
    POSTGRES_DB_NAME: str
    POSTGRES_DB_USER: str
    POSTGRES_DB_PASSWORD: str

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()   

