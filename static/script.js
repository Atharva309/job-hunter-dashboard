document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navJobs = document.getElementById('nav-jobs');
    const navComps = document.getElementById('nav-companies');
    const viewJobs = document.getElementById('view-jobs');
    const viewComps = document.getElementById('view-companies');
    const pageTitle = document.getElementById('page-title');

    navJobs.addEventListener('click', () => {
        navJobs.classList.add('active');
        navComps.classList.remove('active');
        viewJobs.classList.add('active');
        viewComps.classList.remove('active');
        pageTitle.textContent = "Matched Jobs";
        fetchJobs();
    });

    navComps.addEventListener('click', () => {
        navComps.classList.add('active');
        navJobs.classList.remove('active');
        viewComps.classList.add('active');
        viewJobs.classList.remove('active');
        pageTitle.textContent = "Company Tracker";
        fetchCompanies();
    });

    // Toast Notification
    const showToast = (message) => {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3500);
    };

    // Scan Logic
    const scanBtn = document.getElementById('btn-scan');
    const scanStatus = document.getElementById('scan-status');

    scanBtn.addEventListener('click', async () => {
        try {
            scanBtn.disabled = true;
            scanStatus.textContent = "Scanning...";
            scanStatus.className = "status-badge scanning";
            
            const req = await fetch('/api/scan', { method: 'POST' });
            const data = await req.json();
            
            // Show the backend's message
            if (data.status === "error") {
                showToast("⚠️ " + (data.message || "Scan error"));
            } else {
                showToast("✅ " + (data.message || "Scan complete!"));
            }
            
            // Refresh data immediately
            fetchJobs();
            fetchCompanies();
        } catch (e) {
            showToast("❌ Failed to run scan: " + e.message);
        } finally {
            scanBtn.disabled = false;
            scanStatus.textContent = "Idle";
            scanStatus.className = "status-badge idle";
        }
    });

    // Add Company Form
    const form = document.getElementById('add-company-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('company-name').value;
        const url = document.getElementById('company-url').value;

        try {
            const res = await fetch('/api/add-company', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, url })
            });

            if (res.ok) {
                showToast(`Added ${name} to tracker!`);
                form.reset();
                fetchCompanies();
            }
        } catch (e) {
            showToast("Error adding company");
        }
    });

    // Fetch and Render Jobs
    async function fetchJobs() {
        try {
            const res = await fetch('/api/jobs');
            const jobs = await res.json();
            const container = document.getElementById('jobs-container');
            const emptyState = document.getElementById('jobs-empty-state');

            if (jobs.length === 0) {
                container.innerHTML = '';
                container.appendChild(emptyState);
                return;
            }

            container.innerHTML = '';
            jobs.forEach(job => {
                const card = document.createElement('div');
                card.className = 'job-card';

                // Extract URL if Claude put it in parenthesis or returned raw string
                let applyHref = job.apply_link || "";
                if (typeof applyHref === 'string' && applyHref.includes('(')) {
                    applyHref = applyHref.match(/\((.*?)\)/)?.[1] || applyHref;
                }

                card.innerHTML = `
                    <div class="job-company">${job.company}</div>
                    <h2 class="job-title">${job.title}</h2>
                    <div class="job-meta">
                        <span class="tag">${job.location}</span>
                        ${job.sponsorship === 'Yes' ? `<span class="tag sponsor">✓ Sponsorship Mentioned</span>` : ''}
                        <span class="tag">Score: ${job.score}/10</span>
                        <span class="tag">Posted: ${job.date_posted}</span>
                    </div>
                    <p class="job-notes"><strong>Notes:</strong> ${job.notes}</p>
                    <a href="${applyHref.startsWith('http') ? applyHref : job.url}" target="_blank" class="btn-apply">View & Apply Application</a>
                `;
                container.appendChild(card);
            });
        } catch (e) {
            console.error(e);
        }
    }

    // Fetch and Render Companies
    async function fetchCompanies() {
        try {
            const res = await fetch('/api/companies');
            const companies = await res.json();
            const tbody = document.getElementById('companies-tbody');
            tbody.innerHTML = '';

            companies.forEach(company => {
                const row = document.createElement('tr');
                
                // Determine styling based on status string (Found Jobs, No Matches, Pending, Error)
                let statusClass = "status-Pending";
                if (company.status.includes('Found')) statusClass = "status-Found";
                if (company.status.includes('No')) statusClass = "status-No";
                if (company.status.includes('Error')) statusClass = "status-Error";

                row.innerHTML = `
                    <td><strong>${company.name}</strong></td>
                    <td><a href="${company.url}" target="_blank">${company.url}</a></td>
                    <td><span class="status-cell ${statusClass}">${company.status}</span></td>
                `;
                tbody.appendChild(row);
            });
        } catch (e) {
            console.error(e);
        }
    }

    // Initial Load
    fetchJobs();
});
