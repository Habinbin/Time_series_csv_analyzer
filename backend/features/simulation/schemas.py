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
    csv_start_year: int = 2025
    csv_start_month: int = 1
    csv_start_day: int = 1
    csv_end_year: int = 2025
    csv_end_month: int = 12
    csv_end_day: int = 31

class DownsampledResultResponse(BaseModel):
    data: Dict[str, List[Union[float, None]]]
