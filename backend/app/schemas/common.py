from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page[T](ApiModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class Message(ApiModel):
    message: str
