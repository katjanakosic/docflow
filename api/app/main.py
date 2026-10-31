from fastapi import FastAPI

from app.api import documents

app = FastAPI(title="DocFlow API")
app.include_router(documents.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
