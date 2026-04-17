from pydantic import BaseModel
from typing import List, Dict, Any, Union

class VariableInfo(BaseModel):
    name: str
    unit: str
    raw_col: str

class DownsampledResultRequest(BaseModel):
    variables: List[str]
    threshold: int = 1000  # Number of points to display (LTTB/M4 target)
    xmin: Union[float, None] = None
    xmax: Union[float, None] = None

class DownsampledResultResponse(BaseModel):
    data: Dict[str, List[Union[float, None]]]
