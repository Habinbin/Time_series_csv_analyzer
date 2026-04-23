from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List, Dict, Any
from . import schemas
from . import service

router = APIRouter()

@router.get("/variables", operation_id="simulation_get_variables")
async def get_variables() -> List[Dict[str, str]]:
    """Get all available variables and their units for plotting."""
    return service.get_variables()

@router.post("/results", operation_id="simulation_get_results")
async def get_results(req: schemas.DownsampledResultRequest):
    """
    Fetch downsampled results using LTTB algorithm.
    """
    data = service.get_downsampled_data(
        variables=req.variables,
        threshold=req.threshold,
        xmin=req.xmin,
        xmax=req.xmax,
        csv_start_year=req.csv_start_year,
        csv_start_month=req.csv_start_month,
        csv_start_day=req.csv_start_day,
        csv_end_year=req.csv_end_year,
        csv_end_month=req.csv_end_month,
        csv_end_day=req.csv_end_day,
    )
    return {"data": data}

@router.post("/upload_csv", operation_id="simulation_upload_csv")
def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file and set it as the active dataset.
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    try:
        # FastAPI runs sync endpoints in a threadpool, preventing event loop blocking.
        # file.file is a SpooledTemporaryFile that can be directly passed to pandas.read_csv()
        result = service.process_csv_upload(file.file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
