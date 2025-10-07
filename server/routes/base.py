from fastapi import APIRouter, Depends
from server.config import get_settings, Settings

router = APIRouter()

@router.get("/")
def root(app_settings:Settings = Depends(get_settings)):
        app_name = app_settings.APP_NAME
        app_version = app_settings.APP_VERSION

        return {
            "app_name": app_name, 
            "app_version": app_version
            }   

