document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    const chatWindow = document.getElementById('chatWindow');

    // ── Local Knowledge Base ──
    const knowledgeBase = [
        {
            keywords: ['web', 'application', 'webapp'],
            response: "Web application security focuses on protecting websites from threats like SQL injection, Cross-Site Scripting (XSS), and broken authentication. We test for these using OWASP methodologies."
        },
        {
            keywords: ['api', 'endpoint', 'rest'],
            response: "API security involves protecting the data exchanged between applications. Common risks include Broken Object Level Authorization (BOLA) and excessive data exposure. We assess your APIs for these vulnerabilities."
        },
        {
            keywords: ['owasp', 'top 10'],
            response: "The OWASP Top 10 is a standard awareness document for developers and web application security. It represents a broad consensus about the most critical security risks to web applications, such as Broken Access Control and Injection."
        },
        {
            keywords: ['vulnerability', 'assessment', 'scan'],
            response: "A Vulnerability Assessment is a systematic review of security weaknesses in an information system. It evaluates if the system is susceptible to any known vulnerabilities, assigns severity levels, and recommends remediation."
        },
        {
            keywords: ['penetration', 'pentest', 'ethical', 'hacking'],
            response: "Penetration Testing (or pentesting) is an authorized simulated cyberattack on a computer system, performed to evaluate the security of the system. Imvula Labs only conducts these with strict written authorization."
        },
        {
            keywords: ['secure', 'development', 'sdlc', 'coding'],
            response: "Secure Software Development involves integrating security into every phase of the software development lifecycle (SDLC), from design to deployment, to prevent vulnerabilities before they reach production."
        },
        {
            keywords: ['best practice', 'protection', 'prevent'],
            response: "Cybersecurity best practices include using strong MFA, keeping systems patched, implementing least privilege access, and conducting regular security assessments."
        },
        {
            keywords: ['service', 'offer', 'hire', 'cost', 'price'],
            response: "Imvula Labs offers Web App Testing, API Security, Vulnerability Assessments, and Secure Code Reviews. You can request a consultation via our contact section below."
        },
        {
            keywords: ['imvula', 'labs', 'who are you', 'company'],
            response: "Imvula Labs is a South African cybersecurity company specializing in ethical penetration testing and AI-assisted security intelligence. Our tagline is 'Understand the risk. Prioritise the fix.'"
        }
    ];

    function addMessage(text, isUser) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message ' + (isUser ? 'user-message' : 'ai-message');
        
        if (!isUser) {
            msgDiv.innerHTML = `<strong>Imvula AI</strong><p>${text}</p>`;
        } else {
            msgDiv.innerHTML = `<p>${text}</p>`;
        }
        
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to bottom
    }

    function getResponse(input) {
        const lowerInput = input.toLowerCase();
        
        // Find the best match by counting keyword hits
        let bestMatch = null;
        let maxHits = 0;

        knowledgeBase.forEach(item => {
            let hits = 0;
            item.keywords.forEach(keyword => {
                if (lowerInput.includes(keyword)) hits++;
            });
            
            if (hits > maxHits) {
                maxHits = hits;
                bestMatch = item.response;
            }
        });

        if (bestMatch) {
            return bestMatch;
        } else {
            return "I am a local knowledge base, so I might not understand complex questions yet. Try asking about 'Penetration Testing', 'OWASP', 'API security', or our 'Services'.";
        }
    }

    function handleSend() {
        const text = chatInput.value.trim();
        if (!text) return;

        // 1. Show user message
        addMessage(text, true);
        chatInput.value = '';

        // 2. Simulate typing delay for AI response
        setTimeout(() => {
            const response = getResponse(text);
            addMessage(response, false);
        }, 600);
    }

    // Event listeners
    chatSendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleSend();
    });
});
