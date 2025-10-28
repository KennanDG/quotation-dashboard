from pydantic import BaseModel
from enum import Enum

class ServiceType(str, Enum):
    design = "design"
    pcba = "pcba"
    im = "im"
    prototyping = "prototyping"

class Project(BaseModel):
    id: int | None = None
    name: str
    serviceType: ServiceType
    status: str = "draft"