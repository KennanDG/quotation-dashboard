from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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