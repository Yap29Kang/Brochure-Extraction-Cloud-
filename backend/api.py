from fastapi import FastAPI, UploadFile, File, HTTPException
import traceback
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import shutil, os, json, re
import subprocess

from run_pipeline import process_single_pdf

app = FastAPI()


# Models
class MetaPayload(BaseModel):
    meta: dict


def _normalize_origin(value: str) -> str:
    return value.strip().rstrip("/")


def _get_allowed_origins() -> list[str]:
    # Comma-separated origins from env, e.g. "https://a.vercel.app,https://b.vercel.app"
    env_origins = os.getenv("FRONTEND_ORIGINS", "")
    parsed = [_normalize_origin(v) for v in env_origins.split(",") if v.strip()]

    defaults = [
        "http://localhost:5173",
        "https://keyword-extraction-and-automation.vercel.app",
        "https://text-extraction-from-brochure.vercel.app",
    ]
    merged = parsed + defaults

    # Keep order and remove duplicates.
    seen = set()
    unique = []
    for origin in merged:
        if origin not in seen:
            unique.append(origin)
            seen.add(origin)
    return unique

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root 
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Keyword Extraction & Automation API"
    }


# Upload PDF
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        os.makedirs("temp", exist_ok=True)
        path = f"temp/{file.filename}"

        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return process_single_pdf(path)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Save Draft
@app.post("/draft")
def save_draft(payload: MetaPayload):
    os.makedirs("drafts", exist_ok=True)

    draft = payload.meta
    draft["status"] = "DRAFT"
    draft["saved_at"] = datetime.now().isoformat()

    # SAFE filename (match React payload)
    title = draft.get("program_title", "unknown")
    safe_title = re.sub(r"[^\w\- ]", "_", title)
    filename = f"drafts/{safe_title}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)

    return {"status": "saved", "file": filename}


# Autofill (review only)
@app.post("/autofill")
def autofill_form(payload: MetaPayload):
    subprocess.Popen(
        [
            "python",
            "autofill.py",  
            json.dumps(payload.meta)
        ],
        cwd=os.path.dirname(__file__)
    )

    return {"status": "autofill_started"}



