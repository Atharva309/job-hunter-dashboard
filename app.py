from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import pathlib
import traceback

import db
from job_agent import process_jobs, process_single_company

app = FastAPI(title="Job Hunter Dashboard")

BASE_DIR = pathlib.Path(__file__).parent.resolve()

# Initialize database on startup
db.init_db()

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

class CompanyPayload(BaseModel):
    name: str
    url: str

class AppliedPayload(BaseModel):
    company: str
    title: str
    apply_link: str = ""
    location: str = ""

# --- Routes ---
@app.get("/")
def serve_index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))

@app.get("/api/jobs")
def get_jobs():
    rows = db.get_all_jobs()
    return [
        {
            "company": r["company_name"],
            "url": r["career_url"],
            "title": r["job_title"],
            "apply_link": r["apply_link"],
            "location": r["location"],
            "sponsorship": r["sponsorship"],
            "entry_level": r["entry_level"],
            "date_posted": r["date_posted"],
            "score": r["match_score"],
            "notes": r["notes"]
        }
        for r in rows
    ]

@app.get("/api/companies")
def get_companies():
    return db.get_all_companies()

@app.post("/api/add-company")
def add_company(payload: CompanyPayload):
    try:
        db.add_company(payload.name, payload.url)
        return {"status": "success", "message": f"Added {payload.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/companies/{company_name}")
def delete_company(company_name: str):
    deleted = db.delete_company(company_name)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
    return {"status": "success", "message": f"Removed {company_name}"}

@app.post("/api/scan")
def trigger_scan():
    try:
        result = process_jobs()
        if result is None:
            return {"status": "success", "message": "Scan finished."}
        if result.get("status") == "error":
            return {"status": "error", "message": result.get("message", "Unknown error")}
        return {"status": "success", "message": result.get("message", "Scan complete")}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"SCAN ERROR: {tb}")
        return {"status": "error", "message": str(e)}

@app.post("/api/scan/{company_name}")
def scan_single(company_name: str):
    try:
        result = process_single_company(company_name)
        if result is None:
            return {"status": "success", "message": "Scan finished."}
        if result.get("status") == "error":
            return {"status": "error", "message": result.get("message", "Unknown error")}
        return {"status": "success", "message": result.get("message", "Scan complete")}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"SCAN ERROR: {tb}")
        return {"status": "error", "message": str(e)}

# --- Applied Jobs ---
@app.get("/api/applied")
def get_applied():
    jobs = db.get_applied()
    return {"count": len(jobs), "jobs": jobs}

@app.post("/api/applied")
def mark_applied(payload: AppliedPayload):
    db.add_applied(payload.company, payload.title, payload.apply_link, payload.location)
    db.mark_job_applied(payload.company, payload.title)
    jobs = db.get_applied()
    return {"status": "success", "count": len(jobs), "message": f"Marked as applied: {payload.title} @ {payload.company}"}

@app.delete("/api/applied/{applied_id}")
def remove_applied(applied_id: int):
    deleted = db.remove_applied(applied_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Not found")
    jobs = db.get_applied()
    return {"status": "success", "count": len(jobs), "message": "Removed from applied list"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5050))
    uvicorn.run(app, host="0.0.0.0", port=port)
