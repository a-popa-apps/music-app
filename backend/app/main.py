from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Quickie Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the Vercel domain once it's live
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
