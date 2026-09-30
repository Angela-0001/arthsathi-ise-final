from pydantic import BaseModel
from typing import Optional, List


class SchemeOut(BaseModel):
    scheme_id: str
    name: str
    description: str
    ministry: Optional[str]
    category: Optional[str]
    benefit_value: Optional[float]
    application_url: Optional[str]
    translated_name: Optional[str] = None
    translated_description: Optional[str] = None

    class Config:
        from_attributes = True
