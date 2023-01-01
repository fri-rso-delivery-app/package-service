from pydantic import BaseModel


class Distance(BaseModel):
    p1: str
    p2: str
    distance: int
    duration: int


class DistanceList(BaseModel):
    __root__: list[Distance]
