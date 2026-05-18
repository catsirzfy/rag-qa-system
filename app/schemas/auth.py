from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int; username: str; email: str; role: str; is_active: bool
    class Config: from_attributes = True
