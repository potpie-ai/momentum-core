from datetime import datetime

from pydantic import BaseModel


class CreateUser(BaseModel):
    uid: str
    email: str
    display_name: str
    email_verified: bool
    created_at: datetime
    last_login_at: datetime
    provider_info: dict
    provider_username: str
