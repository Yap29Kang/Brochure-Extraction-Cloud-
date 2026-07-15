from fastapi import FastAPI, UploadFile, File, HTTPException
import traceback
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import shutil, os, json, re
import subprocess
import sys
import uvicorn
from fastapi.responses import Response

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


@app.head("/")
def root_head():
    return Response(status_code=200)


@app.get("/health")
def health():
    return {"status": "ok"}


# Upload PDF
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        # Lazy import to keep API startup fast so the server can bind the port quickly.
        from run_pipeline import process_single_pdf

        os.makedirs("temp", exist_ok=True)
        path = f"temp/{file.filename}"

        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        print(f"[Upload] Starting processing for {file.filename}")
        result = process_single_pdf(path)
        print(f"[Upload] Success for {file.filename}")
        return result

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[Upload] ERROR for {file.filename}: {error_type}: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{error_type}: {error_msg}")

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
            sys.executable,
            "autofill.py",  
            json.dumps(payload.meta)
        ],
        cwd=os.path.dirname(__file__)
    )

    return {"status": "autofill_started"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port)



