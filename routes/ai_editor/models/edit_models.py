from pydantic import BaseModel


class EditElementResponse(BaseModel):
    html_content: str
    response: str
    status: str

