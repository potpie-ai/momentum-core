from pydantic import BaseModel


class GenerateTests(BaseModel):
    identifier: str
    endpoint_path: str
    project_id: int
