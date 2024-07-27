from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, root_validator

class RepoDetails(BaseModel):
    repo_name: Optional[str] = Field(default=None)
    repo_path: Optional[str] = Field(default=None)
    branch_name: str

    def __init__(self, **data):
        super().__init__(**data)
        if not self.repo_name and not self.repo_path:
            raise ValueError('Either repo_name or repo_path must be provided.')

class EndpointDetails(RepoDetails):
    endpoint_id: str


class NodeDetails(RepoDetails):
    node_id: str


class BlastRadiusDetails(RepoDetails):
    base_branch: str = 'main'


class TestPlan(BaseModel):
    happy_path: List[str]
    edge_case: List[str]


class TestPlanDetails(BaseModel):
    plan: TestPlan
    project_id: int
    identifier: str


class PreferenceDetails(BaseModel):
    preference: str
    identifier: str
    project_id: int


class GetTestPlan(BaseModel):
    identifier: str

class ProjectStatusEnum(str, Enum):
    CREATED = 'created'
    READY = 'ready' 
    ERROR = 'error'


