document.addEventListener("DOMContentLoaded", () => {
    const terminal = document.getElementById("terminal");
    const terminalMessages = [
        "connecting to authorized security environment...",
        "loading threat intelligence modules...",
        "mapping application attack surface...",
        "checking authentication controls...",
        "analyzing security configuration...",
        "calculating risk indicators...",
        "generating security recommendations...",
        "security analysis complete ✓"
    ];
    let terminalIndex = 0;
    function addTerminalLine(message) {
        const line = document.createElement("div");
        line.className = "terminal-line";
        line.innerHTML = `<span class="prompt">$</span> ${message}`;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    }
    function runTerminal() {
        if (terminalIndex >= terminalMessages.length) {
            setTimeout(() => {
                terminal.innerHTML = "";
                terminalIndex = 0;
                runTerminal();
            }, 3500);
            return;
        }
        addTerminalLine(terminalMessages[terminalIndex]);
        terminalIndex++;
        setTimeout(runTerminal, 850);
    }
    if (terminal) {
        terminal.innerHTML = "";
        runTerminal();
    }
    const menuToggle = document.getElementById("menuToggle");
    const navMenu = document.getElementById("navMenu");
    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            navMenu.classList.toggle("open");
        });
        navMenu.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                navMenu.classList.remove("open");
            });
        });
    }
    const revealElements = document.querySelectorAll(".service-card, .process-step, .assistant, .about-box");
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });
    revealElements.forEach(element => {
        element.style.opacity = "0";
        element.style.transform = "translateY(25px)";
        element.style.transition = "opacity .7s ease, transform .7s ease";
        observer.observe(element);
    });
    const assistantButton = document.querySelector(".assistant-input button");
    if (assistantButton) {
        assistantButton.addEventListener("click", () => {
            assistantButton.textContent = "✓";
            setTimeout(() => { assistantButton.textContent = "→"; }, 1500);
        });
    }
    console.log("🛡️ Imvula Labs Security Interface Online — DEMO MODE");
});
