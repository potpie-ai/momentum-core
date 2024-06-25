from typing import Optional, List
from enum import Enum

from pydantic import BaseModel


class RepoDetails(BaseModel):
    repo_name: str
    branch_name: str


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


