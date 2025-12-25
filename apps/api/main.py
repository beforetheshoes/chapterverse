from fastapi import FastAPI

app = FastAPI(
    title="ChapterVerse API",
    description="API for the ChapterVerse book tracking application",
    version="0.1.0",
)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/version")
async def version() -> dict[str, str]:
    return {"version": "0.1.0"}
