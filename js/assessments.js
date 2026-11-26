(function () {
    if (!window.ImvulaAuth || !window.ImvulaAuth.isLoggedIn()) {
        window.location.href = window.IMVULA.url("pages/login.html");
        return;
    }

    document.getElementById("logoutLink")?.addEventListener("click", (e) => {
        e.preventDefault();
        window.ImvulaAuth.logout();
    });

    function esc(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        }[c]));
    }

    const listContainer = document.getElementById("assessmentsList");
    if (listContainer) {
        const formContainer = document.getElementById("newAssessmentForm");
        const newBtn = document.getElementById("newAssessmentBtn");
        const cancelBtn = document.getElementById("cancelBtn");
        const form = document.getElementById("assessmentForm");
        const errBox = document.getElementById("formError");

        function loadAssessments() {
            listContainer.innerHTML = '<p style="color:#94a3b8;">Loading...</p>';
            window.ImvulaAuth.api("/assessments").then(data => {
                if (!data || data.length === 0) {
                    listContainer.innerHTML = '<p style="color:#94a3b8;">No assessments yet. Create one above.</p>';
                    return;
                }
                listContainer.innerHTML = data.map(a => `
                    <div class="assessment-card">
                        <div>
                            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:12px;">
                                <h4>${esc(a.name)}</h4>
                                <span class="badge ${esc(a.status)}">${esc(a.status).replace('_', ' ')}</span>
                            </div>
                            <p><strong style="color:#e2e8f0;">Target:</strong> ${esc(a.target)}</p>
                            <p><strong style="color:#e2e8f0;">Type:</strong> ${esc(a.assessment_type).replace('_', ' ')}</p>
                            <p><strong style="color:#e2e8f0;">Date:</strong> ${new Date(a.created_at).toLocaleDateString()}</p>
                        </div>
                        <div style="margin-top:15px; padding-top:15px; border-top:1px solid #1e293b; text-align:right;">
                            <a href="assessment-detail.html?id=${a.id}" style="color:#00ff9d; text-decoration:none; font-size:14px; font-weight:600;">View Details →</a>
                        </div>
                    </div>
                `).join("");
            }).catch(err => {
                listContainer.innerHTML = `<p style="color:#ef4444;">Error: ${esc(err.message)}</p>`;
            });
        }

        newBtn.addEventListener("click", () => {
            formContainer.style.display = "block";
            newBtn.style.display = "none";
        });
        
        cancelBtn.addEventListener("click", () => {
            formContainer.style.display = "none";
            newBtn.style.display = "block";
            errBox.style.display = "none";
        });

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            errBox.style.display = "none";
            const body = {
                name: document.getElementById("assessName").value.trim(),
                target: document.getElementById("assessTarget").value.trim(),
                assessment_type: document.getElementById("assessType").value,
                scope: document.getElementById("assessScope").value.trim(),
                authorisation_proof: document.getElementById("assessProof").value.trim(),
            };
            
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting...";

            window.ImvulaAuth.api("/assessments", { method: "POST", body })
                .then(() => { 
                    form.reset(); 
                    formContainer.style.display = "none"; 
                    newBtn.style.display = "block";
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Submit Assessment";
                    loadAssessments(); 
                })
                .catch(err => {
                    errBox.textContent = err.message || "Failed to create assessment";
                    errBox.style.display = "block";
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Submit Assessment";
                });
        });

        loadAssessments();
    }

    const detailContainer = document.getElementById("assessmentDetail");
    if (detailContainer) {
        const params = new URLSearchParams(window.location.search);
        const id = params.get("id");
        if (!id) { 
            detailContainer.innerHTML = "<p style='color:#ef4444;'>No assessment ID provided.</p>"; 
            return; 
        }

        Promise.all([
            window.ImvulaAuth.api(`/assessments/${id}`),
            window.ImvulaAuth.api(`/assessments/${id}/findings`)
        ]).then(([assessment, findings]) => {
            let findingsHtml = findings.length === 0 
                ? '<p style="color:#94a3b8;">No findings recorded yet.</p>' 
                : findings.map(f => `
                    <div style="background:#0f172a; border-left: 4px solid #${f.severity === 'critical' ? 'ef4444' : f.severity === 'high' ? 'f97316' : f.severity === 'medium' ? 'eab308' : '00ff9d'}; padding: 15px; margin-bottom: 10px; border-radius: 4px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                            <strong style="color:#fff;">${esc(f.title)}</strong>
                            <span class="badge ${esc(f.severity)}">${esc(f.severity)}</span>
                        </div>
                        <p style="color:#94a3b8; margin:0 0 10px 0; font-size:13px;">${esc(f.description) || 'No description'}</p>
                        <div style="background:#1e293b; padding:10px; border-radius:4px;">
                            <strong style="color:#00ff9d; font-size:12px;">Remediation:</strong>
                            <p style="color:#e2e8f0; margin:5px 0 0 0; font-size:13px;">${esc(f.remediation) || 'Pending recommendation'}</p>
                        </div>
                    </div>
                `).join("");

            detailContainer.innerHTML = `
                <div class="page-header" style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <h1>${esc(assessment.name)}</h1>
                        <p style="color:#94a3b8; margin:5px 0 0 0;">Target: ${esc(assessment.target)}</p>
                    </div>
                    <span class="badge ${esc(assessment.status)}">${esc(assessment.status).replace('_', ' ')}</span>
                </div>
                
                <div class="detail-card" style="margin-top:20px;">
                    <h3 style="color:#fff; margin-top:0; margin-bottom:15px;">Assessment Information</h3>
                    <div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">${esc(assessment.assessment_type).replace('_', ' ')}</span></div>
                    <div class="detail-row"><span class="detail-label">Created</span><span class="detail-value">${new Date(assessment.created_at).toLocaleString()}</span></div>
                    <div class="detail-row"><span class="detail-label">Scope</span><span class="detail-value">${esc(assessment.scope) || 'Not specified'}</span></div>
                    <div class="detail-row"><span class="detail-label">Authorisation Proof</span><span class="detail-value">${esc(assessment.authorisation_proof)}</span></div>
                </div>

                <div class="detail-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <h3 style="color:#fff; margin:0;">Findings (${findings.length})</h3>
                    </div>
                    ${findingsHtml}
                </div>
            `;
        }).catch(err => {
            detailContainer.innerHTML = `<p style="color:#ef4444;">Error loading details: ${esc(err.message)}</p>`;
        });
    }
})();
