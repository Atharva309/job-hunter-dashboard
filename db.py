import os
import psycopg2
from psycopg2.extras import RealDictCursor

import urllib.parse

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    """Get a database connection."""
    # Handle special characters in password by properly URL encoding them
    url = DATABASE_URL
    if url and "@" in url:
        try:
            # Format: postgresql://user:pass@host:port/db
            schema_part, rest = url.split("://", 1)
            auth_part, host_part = rest.split("@", 1)
            
            if ":" in auth_part:
                user, pwd = auth_part.split(":", 1)
                # If password contains special chars but isn't URL-encoded yet
                if "%" not in pwd or " " in pwd:  # basic heuristic
                    pwd = urllib.parse.quote(pwd)
                url = f"{schema_part}://{user}:{pwd}@{host_part}"
        except Exception:
            pass # Fallback to raw URL if parsing fails
            
    return psycopg2.connect(url)

def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            company_name TEXT NOT NULL,
            career_url TEXT,
            job_title TEXT,
            apply_link TEXT,
            location TEXT,
            sponsorship TEXT,
            entry_level TEXT,
            date_posted TEXT,
            match_score TEXT,
            status TEXT DEFAULT '',
            notes TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applied (
            id SERIAL PRIMARY KEY,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            apply_link TEXT DEFAULT '',
            location TEXT DEFAULT '',
            applied_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# --- Company / Job Operations ---

def get_all_jobs():
    """Get all matched jobs (not applied, not errors)."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM jobs 
        WHERE job_title IS NOT NULL 
          AND job_title != '' 
          AND job_title NOT LIKE '%%No matches%%'
          AND job_title NOT LIKE '%%Error%%'
          AND job_title NOT LIKE '%%Failed%%'
          AND (status IS NULL OR status != 'Applied')
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_all_companies():
    """Get unique companies with their scan status."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT ON (company_name) 
            company_name, career_url, job_title, status
        FROM jobs 
        WHERE company_name IS NOT NULL
        ORDER BY company_name, id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    companies = []
    for r in rows:
        title = r["job_title"] or ""
        s = "Pending"
        if "No matches" in title:
            s = "No Matches"
        elif "Error" in title or "Failed" in title:
            s = "Error"
        elif title:
            s = "Found Jobs"
        
        companies.append({
            "name": r["company_name"],
            "url": r["career_url"],
            "status": s
        })
    return companies

def add_company(name, url):
    """Add a new company to track."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs (company_name, career_url) VALUES (%s, %s)", (name, url))
    conn.commit()
    cur.close()
    conn.close()

def delete_company(name):
    """Remove all rows for a company."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs WHERE company_name = %s AND (status IS NULL OR status != 'Applied')", (name,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted

def get_company_rows_for_scan():
    """Get companies that need to be scanned (no title or error status)."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, company_name, career_url FROM jobs
        WHERE (status IS NULL OR status != 'Applied')
          AND (job_title IS NULL OR job_title = '' OR job_title LIKE '%%Error%%' OR job_title LIKE '%%Failed%%')
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_company_row_for_single_scan(company_name):
    """Get a single company row to scan, or its URL if all are applied."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Try to find a non-applied row
    cur.execute("""
        SELECT id, career_url FROM jobs 
        WHERE company_name = %s AND (status IS NULL OR status != 'Applied')
        ORDER BY id LIMIT 1
    """, (company_name,))
    row = cur.fetchone()
    
    if row:
        cur.close()
        conn.close()
        return {"id": row["id"], "url": row["career_url"], "is_new": False}
    
    # All rows are applied — get the URL from any row and create a fresh one
    cur.execute("SELECT career_url FROM jobs WHERE company_name = %s LIMIT 1", (company_name,))
    existing = cur.fetchone()
    
    if not existing:
        cur.close()
        conn.close()
        return None
    
    url = existing["career_url"]
    cur.execute("INSERT INTO jobs (company_name, career_url) VALUES (%s, %s) RETURNING id", (company_name, url))
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "url": url, "is_new": True}

def clear_job_row(row_id):
    """Clear scan results for a row (preserving company info and status)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs SET job_title=NULL, apply_link=NULL, location=NULL, 
            sponsorship=NULL, entry_level=NULL, date_posted=NULL, 
            match_score=NULL, notes=NULL
        WHERE id = %s AND (status IS NULL OR status != 'Applied')
    """, (row_id,))
    conn.commit()
    cur.close()
    conn.close()

def write_job_result(row_id, job_data):
    """Write a single job result to a row."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs SET 
            job_title=%s, apply_link=%s, location=%s, sponsorship=%s,
            entry_level=%s, date_posted=%s, match_score=%s, notes=%s
        WHERE id = %s
    """, (
        job_data.get("job_title", ""),
        job_data.get("apply_link", ""),
        job_data.get("location", ""),
        job_data.get("sponsorship", ""),
        job_data.get("entry_level", ""),
        job_data.get("date_posted", ""),
        str(job_data.get("match_score", "")),
        job_data.get("notes", ""),
        row_id
    ))
    conn.commit()
    cur.close()
    conn.close()

def insert_extra_job(company_name, url, job_data):
    """Insert an additional job row for a company (when Claude finds multiple matches)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (company_name, career_url, job_title, apply_link, location, 
            sponsorship, entry_level, date_posted, match_score, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        company_name, url,
        job_data.get("job_title", ""),
        job_data.get("apply_link", ""),
        job_data.get("location", ""),
        job_data.get("sponsorship", ""),
        job_data.get("entry_level", ""),
        job_data.get("date_posted", ""),
        str(job_data.get("match_score", "")),
        job_data.get("notes", "")
    ))
    conn.commit()
    cur.close()
    conn.close()

def set_job_status(row_id, status_text):
    """Set the job_title (used as status indicator for non-match rows)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET job_title = %s WHERE id = %s", (status_text, row_id))
    conn.commit()
    cur.close()
    conn.close()

def mark_job_applied(company, title):
    """Mark a job as Applied in the jobs table."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs SET status = 'Applied' 
        WHERE id = (
            SELECT id FROM jobs 
            WHERE company_name = %s AND job_title = %s AND (status IS NULL OR status != 'Applied')
            LIMIT 1
        )
    """, (company, title))
    conn.commit()
    cur.close()
    conn.close()

def delete_empty_row(row_id):
    """Delete a temporary empty row."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs WHERE id = %s", (row_id,))
    conn.commit()
    cur.close()
    conn.close()

# --- Applied Operations ---

def get_applied():
    """Get all applied jobs."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM applied ORDER BY applied_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Convert datetime to string
    for r in rows:
        if r.get("applied_at"):
            r["applied_at"] = r["applied_at"].isoformat()
    return rows

def add_applied(company, title, apply_link="", location=""):
    """Add a job to the applied list."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO applied (company, title, apply_link, location) 
        VALUES (%s, %s, %s, %s)
    """, (company, title, apply_link, location))
    conn.commit()
    cur.close()
    conn.close()

def remove_applied(applied_id):
    """Remove from applied list by ID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM applied WHERE id = %s", (applied_id,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted

def get_applied_titles_for_company(company_name):
    """Get set of applied job titles for a company (for filtering)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT LOWER(TRIM(title)) FROM applied WHERE company = %s", (company_name,))
    titles = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return titles
