from typing import Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class RESTResponse(BaseModel, Generic[T]):
    code: int = Field(description="HTTP status code")
    success: bool = Field(description="True if request succeeded, False otherwise")
    data: T|None = Field(default=None, description="Payload returned in the response")
    msg: str = Field(description="Detailed message about the response")