from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import openpyxl
import os
import pathlib
import traceback

# Import the core agent logic
from job_agent import process_jobs, EXCEL_FILE, init_excel

app = FastAPI(title="Job Hunter Dashboard")

BASE_DIR = pathlib.Path(__file__).parent.resolve()

# Ensure excel exists on startup
if not os.path.exists(EXCEL_FILE):
    init_excel()

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

class CompanyPayload(BaseModel):
    name: str
    url: str

@app.get("/")
def serve_index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))

@app.get("/api/jobs")
def get_jobs():
    if not os.path.exists(EXCEL_FILE):
        return []
    
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    jobs = []
    
    # Skip header
    for r in range(2, ws.max_row + 1):
        matched = ws.cell(row=r, column=3).value
        # Only return rows that have actual job matches (not empty, not errors, not 'No matches found')
        if matched and matched != "No matches found" and "Error" not in str(matched) and "Failed" not in str(matched):
            jobs.append({
                "company": ws.cell(row=r, column=1).value,
                "url": ws.cell(row=r, column=2).value,
                "title": matched,
                "apply_link": ws.cell(row=r, column=4).value,
                "location": ws.cell(row=r, column=5).value,
                "sponsorship": ws.cell(row=r, column=6).value,
                "entry_level": ws.cell(row=r, column=7).value,
                "date_posted": ws.cell(row=r, column=8).value,
                "score": ws.cell(row=r, column=9).value,
                "notes": ws.cell(row=r, column=11).value
            })
    return jobs

@app.get("/api/companies")
def get_companies():
    if not os.path.exists(EXCEL_FILE):
        return []
        
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    companies = []
    
    for r in range(2, ws.max_row + 1):
        name = ws.cell(row=r, column=1).value
        url = ws.cell(row=r, column=2).value
        
        # Avoid duplicate companies in list
        if name and not any(c['name'] == name for c in companies):
            matched = ws.cell(row=r, column=3).value
            status = "Pending"
            if matched == "No matches found":
                status = "No Matches"
            elif matched and ("Error" in str(matched) or "Failed" in str(matched)):
                status = "Error"
            elif matched:
                status = "Found Jobs"
                
            companies.append({
                "name": name,
                "url": url,
                "status": status
            })
            
    return companies

@app.post("/api/add-company")
def add_company(payload: CompanyPayload):
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active
        ws.append([payload.name, payload.url] + [""] * 9)
        wb.save(EXCEL_FILE)
        return {"status": "success", "message": f"Added {payload.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan")
def trigger_scan():
    """Run the job scan. Wrapped in try/except so it NEVER crashes the server."""
    try:
        result = process_jobs()
        
        # If process_jobs returned None (shouldn't happen, but safety net)
        if result is None:
            return {"status": "success", "message": "Scan finished (no status returned)."}
        
        # If process_jobs reported an error
        if result.get("status") == "error":
            return {"status": "error", "message": result.get("message", "Unknown error")}
        
        return {"status": "success", "message": result.get("message", "Scan complete")}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"SCAN ERROR: {tb}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5050))
    uvicorn.run(app, host="0.0.0.0", port=port)
