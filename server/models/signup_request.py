from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str