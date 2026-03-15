document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navJobs = document.getElementById('nav-jobs');
    const navComps = document.getElementById('nav-companies');
    const navApplied = document.getElementById('nav-applied');
    const viewJobs = document.getElementById('view-jobs');
    const viewComps = document.getElementById('view-companies');
    const viewApplied = document.getElementById('view-applied');
    const pageTitle = document.getElementById('page-title');

    function switchView(activeNav, activeView, title) {
        [navJobs, navComps, navApplied].forEach(n => n.classList.remove('active'));
        [viewJobs, viewComps, viewApplied].forEach(v => v.classList.remove('active'));
        activeNav.classList.add('active');
        activeView.classList.add('active');
        pageTitle.textContent = title;
    }

    navJobs.addEventListener('click', () => { switchView(navJobs, viewJobs, "Matched Jobs"); fetchJobs(); });
    navComps.addEventListener('click', () => { switchView(navComps, viewComps, "Company Tracker"); fetchCompanies(); });
    navApplied.addEventListener('click', () => { switchView(navApplied, viewApplied, "Applied Jobs"); fetchApplied(); });

    // Toast Notification
    const showToast = (message) => {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3500);
    };

    // Scan All Logic
    const scanBtn = document.getElementById('btn-scan');
    const scanStatus = document.getElementById('scan-status');

    scanBtn.addEventListener('click', async () => {
        try {
            scanBtn.disabled = true;
            scanStatus.textContent = "Scanning...";
            scanStatus.className = "status-badge scanning";
            
            const req = await fetch('/api/scan', { method: 'POST' });
            const data = await req.json();
            
            if (data.status === "error") {
                showToast("⚠️ " + (data.message || "Scan error"));
            } else {
                showToast("✅ " + (data.message || "Scan complete!"));
            }
            
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

    // ========== APPLY MODAL LOGIC ==========
    const modal = document.getElementById('apply-modal');
    const modalInfo = document.getElementById('modal-job-info');
    const modalYes = document.getElementById('modal-yes');
    const modalNo = document.getElementById('modal-no');
    let pendingApply = null;

    function openApplyModal(job) {
        pendingApply = job;
        modalInfo.textContent = `${job.title} @ ${job.company}`;
        modal.style.display = 'flex';
    }

    modalNo.addEventListener('click', () => {
        modal.style.display = 'none';
        pendingApply = null;
    });

    modalYes.addEventListener('click', async () => {
        if (!pendingApply) return;
        try {
            const res = await fetch('/api/applied', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company: pendingApply.company,
                    title: pendingApply.title,
                    apply_link: pendingApply.apply_link || "",
                    location: pendingApply.location || ""
                })
            });
            const data = await res.json();
            showToast("✅ " + data.message);
            updateAppliedCount(data.count);
        } catch (e) {
            showToast("❌ Failed to mark as applied");
        }
        modal.style.display = 'none';
        pendingApply = null;
    });

    // Close modal on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            pendingApply = null;
        }
    });

    // ========== FETCH & RENDER JOBS ==========
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

                let applyHref = job.apply_link || "";
                if (typeof applyHref === 'string' && applyHref.includes('(')) {
                    applyHref = applyHref.match(/\((.*?)\)/)?.[1] || applyHref;
                }
                const finalUrl = applyHref.startsWith('http') ? applyHref : job.url;

                card.innerHTML = `
                    <div class="job-company">${job.company}</div>
                    <h2 class="job-title">${job.title}</h2>
                    <div class="job-meta">
                        <span class="tag">${job.location || 'N/A'}</span>
                        ${job.sponsorship === 'Yes' ? `<span class="tag sponsor">✓ Sponsorship</span>` : ''}
                        <span class="tag">Score: ${job.score || '?'}/10</span>
                        <span class="tag">Posted: ${job.date_posted || 'N/A'}</span>
                    </div>
                    <p class="job-notes"><strong>Notes:</strong> ${job.notes || 'No notes'}</p>
                    <a href="${finalUrl}" target="_blank" class="btn-apply" data-job-index="apply">View & Apply</a>
                `;

                // When they click Apply, open the link AND show the confirmation modal
                const applyBtn = card.querySelector('.btn-apply');
                applyBtn.addEventListener('click', (e) => {
                    // Let the link open normally (target=_blank)
                    // Then show the modal after a brief delay
                    setTimeout(() => openApplyModal(job), 500);
                });

                container.appendChild(card);
            });
        } catch (e) {
            console.error(e);
        }
    }

    // ========== FETCH & RENDER COMPANIES ==========
    async function fetchCompanies() {
        try {
            const res = await fetch('/api/companies');
            const companies = await res.json();
            const tbody = document.getElementById('companies-tbody');
            tbody.innerHTML = '';

            companies.forEach(company => {
                const row = document.createElement('tr');
                
                let statusClass = "status-Pending";
                if (company.status.includes('Found')) statusClass = "status-Found";
                if (company.status.includes('No')) statusClass = "status-No";
                if (company.status.includes('Error') || company.status.includes('Failed')) statusClass = "status-Error";

                row.innerHTML = `
                    <td><strong>${company.name}</strong></td>
                    <td><a href="${company.url}" target="_blank">${company.url.length > 50 ? company.url.substring(0, 50) + '...' : company.url}</a></td>
                    <td><span class="status-cell ${statusClass}">${company.status}</span></td>
                    <td>
                        <div class="company-actions">
                            <button class="btn-icon scan-single" title="Scan this company">🔍 Scan</button>
                            <button class="btn-icon delete" title="Remove this company">🗑️ Remove</button>
                        </div>
                    </td>
                `;

                // Single scan button
                row.querySelector('.scan-single').addEventListener('click', async (e) => {
                    const btn = e.target;
                    btn.disabled = true;
                    btn.textContent = "⏳...";
                    scanStatus.textContent = "Scanning...";
                    scanStatus.className = "status-badge scanning";

                    try {
                        const r = await fetch(`/api/scan/${encodeURIComponent(company.name)}`, { method: 'POST' });
                        const data = await r.json();
                        if (data.status === "error") {
                            showToast("⚠️ " + data.message);
                        } else {
                            showToast("✅ " + data.message);
                        }
                        fetchCompanies();
                        fetchJobs();
                    } catch (err) {
                        showToast("❌ Scan failed");
                    } finally {
                        btn.disabled = false;
                        btn.textContent = "🔍 Scan";
                        scanStatus.textContent = "Idle";
                        scanStatus.className = "status-badge idle";
                    }
                });

                // Delete button
                row.querySelector('.delete').addEventListener('click', async () => {
                    if (!confirm(`Remove ${company.name} from tracker?`)) return;
                    try {
                        const r = await fetch(`/api/companies/${encodeURIComponent(company.name)}`, { method: 'DELETE' });
                        if (r.ok) {
                            showToast(`🗑️ Removed ${company.name}`);
                            fetchCompanies();
                            fetchJobs();
                        }
                    } catch (err) {
                        showToast("❌ Failed to remove");
                    }
                });

                tbody.appendChild(row);
            });
        } catch (e) {
            console.error(e);
        }
    }

    // ========== FETCH & RENDER APPLIED ==========
    function updateAppliedCount(count) {
        document.getElementById('applied-count').textContent = count;
        document.getElementById('applied-total').textContent = `Total: ${count}`;
    }

    async function fetchApplied() {
        try {
            const res = await fetch('/api/applied');
            const data = await res.json();
            updateAppliedCount(data.count);

            const container = document.getElementById('applied-container');
            const emptyState = document.getElementById('applied-empty-state');

            if (data.jobs.length === 0) {
                container.innerHTML = '';
                container.appendChild(emptyState);
                return;
            }

            container.innerHTML = '';
            data.jobs.forEach((job, index) => {
                const item = document.createElement('div');
                item.className = 'applied-item';
                
                const date = job.applied_at ? new Date(job.applied_at).toLocaleDateString() : '';
                
                item.innerHTML = `
                    <div class="applied-info">
                        <strong>${job.title}</strong>
                        <small>${job.company} · ${job.location || 'N/A'} · Applied ${date}</small>
                    </div>
                    <button class="btn-remove" data-index="${index}">Remove</button>
                `;

                item.querySelector('.btn-remove').addEventListener('click', async () => {
                    try {
                        const r = await fetch(`/api/applied/${index}`, { method: 'DELETE' });
                        const result = await r.json();
                        updateAppliedCount(result.count);
                        fetchApplied();
                        showToast("Removed from applied list");
                    } catch (err) {
                        showToast("❌ Failed to remove");
                    }
                });

                container.appendChild(item);
            });
        } catch (e) {
            console.error(e);
        }
    }

    // Initial Load
    fetchJobs();
    fetchApplied(); // Load count for sidebar badge
});
