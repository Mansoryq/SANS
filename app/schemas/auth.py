from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class UserLogin(BaseModel):
    username: str
    password: str
