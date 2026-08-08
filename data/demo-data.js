const DEMO = {
    company: {
        name: "Imvula Labs",
        tagline: "We break your web apps before criminals do.",
        email: "info@imvulalabs.co.za",
        demo: true
    },
    dashboard: {
        riskScore: 94,
        totalAssets: 12,
        vulnerabilitiesFound: 47,
        criticalCount: 1,
        highCount: 5,
        mediumCount: 18,
        lowCount: 23,
        assessmentsCompleted: 8,
        lastAssessment: "2026-08-01",
        demo: true
    },
    vulnerabilities: [
        {
            id: "VULN-001",
            title: "SQL Injection in Login Form",
            severity: "Critical",
            cvss: 9.8,
            asset: "webapp.example.com/login",
            status: "Open",
            discovered: "2026-07-28",
            description: "The login form accepts unsanitized user input passed directly to a SQL query.",
            impact: "Complete database compromise. Attacker can extract all user credentials.",
            remediation: "Implement parameterized queries. Validate and sanitize all user input.",
            demo: true
        },
        {
            id: "VULN-002",
            title: "Stored Cross-Site Scripting (XSS)",
            severity: "High",
            cvss: 7.5,
            asset: "webapp.example.com/profile",
            status: "Open",
            discovered: "2026-07-28",
            description: "User profile fields accept and render unsanitized input.",
            impact: "Session hijacking, credential theft, defacement.",
            remediation: "Escape output. Implement Content Security Policy. Validate input.",
            demo: true
        },
        {
            id: "VULN-003",
            title: "Broken Access Control / IDOR",
            severity: "High",
            cvss: 7.1,
            asset: "api.example.com/users/",
            status: "In Progress",
            discovered: "2026-07-29",
            description: "Changing user ID in API requests grants access to other users' data.",
            impact: "Unauthorized access to all user data.",
            remediation: "Implement server-side authorization checks for every request.",
            demo: true
        },
        {
            id: "VULN-004",
            title: "Exposed AWS S3 Bucket",
            severity: "Medium",
            cvss: 5.3,
            asset: "storage.example.com",
            status: "Resolved",
            discovered: "2026-07-15",
            description: "S3 bucket containing application assets is publicly accessible.",
            impact: "Exposure of internal documents and configuration files.",
            remediation: "Apply bucket policies. Enable block public access.",
            demo: true
        },
        {
            id: "VULN-005",
            title: "Missing HTTP Security Headers",
            severity: "Low",
            cvss: 3.1,
            asset: "webapp.example.com",
            status: "Open",
            discovered: "2026-07-30",
            description: "Key security headers not set in server responses.",
            impact: "Exposure to clickjacking, MIME sniffing, MITM attacks.",
            remediation: "Configure web server to include security headers in all responses.",
            demo: true
        }
    ],
    assets: [
        { id: "AST-001", name: "Main Web Application", url: "webapp.example.com", type: "Web App", risk: "Medium", demo: true },
        { id: "AST-002", name: "Customer API", url: "api.example.com", type: "API", risk: "High", demo: true },
        { id: "AST-003", name: "Admin Portal", url: "admin.example.com", type: "Web App", risk: "Critical", demo: true },
        { id: "AST-004", name: "Payment Gateway", url: "pay.example.com", type: "API", risk: "Low", demo: true },
        { id: "AST-005", name: "Cloud Storage", url: "storage.example.com", type: "Cloud", risk: "Medium", demo: true }
    ],
    assessments: [
        { id: "ASM-001", name: "Q3 Web Application Pentest", target: "webapp.example.com", date: "2026-08-01", status: "Completed", findings: 12, demo: true },
        { id: "ASM-002", name: "API Security Review", target: "api.example.com", date: "2026-07-15", status: "Completed", findings: 8, demo: true },
        { id: "ASM-003", name: "Cloud Infrastructure Audit", target: "*.example.com", date: "2026-07-01", status: "In Progress", findings: 5, demo: true }
    ],
    reports: [
        { id: "RPT-001", name: "Q3 Web App Pentest Report", date: "2026-08-01", type: "Pentest", status: "Final", demo: true },
        { id: "RPT-002", name: "API Security Assessment Report", date: "2026-07-20", type: "Assessment", status: "Draft", demo: true },
        { id: "RPT-003", name: "Vulnerability Summary Aug 2026", date: "2026-08-05", type: "Summary", status: "Final", demo: true }
    ]
};
Object.freeze(DEMO);
Object.freeze(DEMO.vulnerabilities);
Object.freeze(DEMO.assets);
Object.freeze(DEMO.assessments);
Object.freeze(DEMO.reports);
