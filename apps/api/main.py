from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.quotes import router as quotes_router
from routers.projects import router as projects_router



app = FastAPI(title="Quotation Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes_router)
app.include_router(projects_router)


@app.get("/")
def root():
    return {"message": "Quotation Dashboard API running"}


@app.get("/health")
def health():
    return {"status": "ok"}





@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    # Use only in dev
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": exc.__class__.__name__},
    )