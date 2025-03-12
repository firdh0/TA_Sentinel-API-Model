from pydantic import BaseModel


class Messages(BaseModel):
    text: list[str]

class Url(BaseModel):
    text: list[str]

class SessionName(BaseModel):
    session_name: str

class TokenUpdate(BaseModel):
    token: str
