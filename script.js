/* ── Existing Imvula Labs Interactions ── */
document.addEventListener('DOMContentLoaded', function () {
    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function () {
            navMenu.classList.toggle('active');
        });
    }

    // Terminal typing animation (existing hero panel)
    const terminal = document.getElementById('terminal');
    if (terminal) {
        const lines = [
            '> initializing security engine...',
            '> loading vulnerability database...',
            '> scanning 12 assets...',
            '> 47 findings detected.',
            '> generating report...',
            '> analysis complete.'
        ];
        let lineIndex = 0;
        function typeLine() {
            if (lineIndex >= lines.length) return;
            const div = document.createElement('div');
            div.className = 'terminal-line';
            div.innerHTML = '<span class="prompt">$</span> ' + lines[lineIndex];
            terminal.appendChild(div);
            lineIndex++;
            setTimeout(typeLine, 800);
        }
        setTimeout(typeLine, 600);
    }

    // Adaptive nav link (if user is logged in, show Dashboard)
    const navAuthLink = document.getElementById('navAuthLink');
    if (navAuthLink) {
        try {
            if (localStorage.getItem('imvula_token')) {
                navAuthLink.textContent = 'Dashboard';
                navAuthLink.href = 'pages/dashboard.html';
            }
        } catch (e) {}
    }
});

/* ── Simulated Security Assessment Demo ── */
(function () {
    const urlInput = document.getElementById('demoUrl');
    const runBtn = document.getElementById('runDemoBtn');
    const errorBox = document.getElementById('demoError');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStage = document.getElementById('progressStage');
    const reportContainer = document.getElementById('reportContainer');
    const reportUrl = document.getElementById('reportUrl');
    const reportScore = document.getElementById('reportScore');
    const reportRiskLevel = document.getElementById('reportRiskLevel');
    const findingsList = document.getElementById('findingsList');
    const recommendationsList = document.getElementById('recommendationsList');
    const resetBtn = document.getElementById('resetDemoBtn');

    if (!urlInput || !runBtn) return; // Demo section not on this page.

    // URL validation regex (allows with or without protocol)
    const urlRegex = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/i;

    function validateUrl(value) {
        const trimmed = value.trim();
        if (!trimmed) return { valid: false, msg: 'Please enter a website URL.' };
        if (!urlRegex.test(trimmed)) return { valid: false, msg: 'Please enter a valid URL (e.g. https://example.com).' };
        return { valid: true, url: trimmed.startsWith('http') ? trimmed : 'https://' + trimmed };
    }

    const stages = [
        { pct: 10, text: 'Initializing assessment engine...' },
        { pct: 30, text: 'Discovering attack surface...' },
        { pct: 55, text: 'Analyzing security configurations...' },
        { pct: 75, text: 'Evaluating vulnerability patterns...' },
        { pct: 90, text: 'Compiling findings...' },
        { pct: 100, text: 'Generating report...' }
    ];

    // Sample report data (clearly labelled as simulated)
    const sampleFindings = [
        { title: 'Missing HTTP Security Headers', severity: 'High', desc: 'Key headers like CSP and HSTS are not set.' },
        { title: 'Outdated TLS Configuration', severity: 'Medium', desc: 'Support for older TLS versions may expose traffic.' },
        { title: 'Verbose Error Messages', severity: 'Low', desc: 'Stack traces may reveal internal paths.' },
        { title: 'No Rate Limiting on Login', severity: 'Critical', desc: 'Brute-force attacks may be possible.' }
    ];

    const sampleRecommendations = [
        'Implement HTTP Strict Transport Security (HSTS) and Content Security Policy (CSP).',
        'Disable TLS 1.0 and 1.1; enforce TLS 1.2 or higher.',
        'Return generic error pages to users; log details server-side only.',
        'Add rate limiting and account lockout to authentication endpoints.'
    ];

    function resetDemo() {
        progressContainer.style.display = 'none';
        reportContainer.style.display = 'none';
        errorBox.style.display = 'none';
        urlInput.value = '';
        progressBar.style.width = '0%';
        progressPercent.textContent = '0%';
        progressStage.textContent = 'Initializing...';
        runBtn.disabled = false;
        runBtn.textContent = 'Run Demo Assessment';
    }

    function showReport(url) {
        reportUrl.textContent = url;
        
        // Generate Date and Ref Number
        const today = new Date();
        const dateStr = today.toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: 'numeric' });
        const refStr = 'IMV-' + today.getFullYear() + '-' + Math.random().toString(36).substring(2, 6).toUpperCase();
        
        if (document.getElementById('reportDate')) document.getElementById('reportDate').textContent = dateStr;
        if (document.getElementById('reportRef')) document.getElementById('reportRef').textContent = refStr;

        // Deterministic pseudo-score based on URL length (simulation only)
        const score = 60 + (url.length % 35); // range 60-95
        reportScore.textContent = score;

        let riskLevel, riskColor;
        if (score >= 80) { riskLevel = 'LOW'; riskColor = '#00ff9d'; }
        else if (score >= 60) { riskLevel = 'MEDIUM'; riskColor = '#eab308'; }
        else { riskLevel = 'HIGH'; riskColor = '#f97316'; }
        reportRiskLevel.textContent = riskLevel;
        reportRiskLevel.style.color = riskColor;

        // Render findings
        findingsList.innerHTML = '';
        sampleFindings.forEach(function (f) {
            const div = document.createElement('div');
            div.className = 'finding-item ' + f.severity.toLowerCase();
            div.innerHTML = `
                <div>
                    <strong style="color:#fff; display:block; margin-bottom:4px;">${f.title}</strong>
                    <span style="color:#94a3b8; font-size:13px;">${f.desc}</span>
                </div>
                <span class="severity-badge ${f.severity.toLowerCase()}">${f.severity}</span>
            `;
            findingsList.appendChild(div);
        });

        // Render recommendations
        recommendationsList.innerHTML = '';
        sampleRecommendations.forEach(function (r) {
            const li = document.createElement('li');
            li.textContent = r;
            recommendationsList.appendChild(li);
        });

        reportContainer.style.display = 'block';
        reportContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function runAssessment() {
        errorBox.style.display = 'none';
        const validation = validateUrl(urlInput.value);
        if (!validation.valid) {
            errorBox.textContent = validation.msg;
            errorBox.style.display = 'block';
            return;
        }

        runBtn.disabled = true;
        runBtn.textContent = 'Assessing...';
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressPercent.textContent = '0%';
        progressStage.textContent = 'Initializing...';

        let stageIndex = 0;
        const interval = setInterval(function () {
            if (stageIndex >= stages.length) {
                clearInterval(interval);
                setTimeout(function () {
                    progressContainer.style.display = 'none';
                    showReport(validation.url);
                    runBtn.disabled = false;
                    runBtn.textContent = 'Run Demo Assessment';
                }, 600);
                return;
            }
            const stage = stages[stageIndex];
            progressBar.style.width = stage.pct + '%';
            progressPercent.textContent = stage.pct + '%';
            progressStage.textContent = stage.text;
            stageIndex++;
        }, 700);
    }

    runBtn.addEventListener('click', runAssessment);
    resetBtn.addEventListener('click', resetDemo);
    
    const printBtn = document.getElementById('printReportBtn');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }

    // Allow Enter key to trigger assessment
    urlInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            runAssessment();
        }
    });
})();
