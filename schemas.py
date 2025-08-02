from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class FilmBase(BaseModel):
    title: str
    genre: str
    price: float


class FilmCreate(FilmBase):
    pass


class FilmRead(FilmBase):
    id: int  # noqa: VNE003

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: str = "user"


class UserRead(UserBase):
    id: int  # noqa: VNE003
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginSchema(BaseModel):
    email: str
    password: str


class PoshtBase(BaseModel):
    title: str
    posht_text: str


class PoshtCreate(PoshtBase):
    title: str = Field(min_length=1)


class PoshtUpdate(PoshtBase):
    pass


class PoshtRead(PoshtBase):
    id: int  # noqa: VNE003
    created_at: datetime
    user_id: int
    is_blocked: bool

    class Config:
        orm_mode = True


class CommentBase(BaseModel):
    comment_text: str


class CommentCreate(CommentBase):
    posht_id: int
    user_id: int


class CommentUpdate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int  # noqa: VNE003
    created_at: datetime
    posht_id: int
    user_id: int
    is_blocked: bool

    class Config:
        orm_mode = True
