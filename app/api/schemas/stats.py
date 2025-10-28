from pydantic import BaseModel
from datetime import date

class DAUItem(BaseModel):
    date: date
    dau: int