from fastapi.responses import JSONResponse\nimport math\nres = JSONResponse({"val": math.nan})\nprint(res.body)
