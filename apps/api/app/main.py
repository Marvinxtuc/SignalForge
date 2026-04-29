from fastapi import FastAPI

app = FastAPI(title="SignalForge API", version="0.1.0-phase-0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "signalforge-api",
        "phase": "phase-0-infrastructure",
    }
