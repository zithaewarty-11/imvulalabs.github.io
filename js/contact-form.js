document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('serviceRequestForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('reqName').value.trim();
        const company = document.getElementById('reqCompany').value.trim();
        const email = document.getElementById('reqEmail').value.trim();
        const service = document.getElementById('reqService').value;
        const desc = document.getElementById('reqDesc').value.trim();
        
        const errorBox = document.getElementById('formError');
        const successBox = document.getElementById('formSuccess');

        // 1. Validation
        if (!name || !email || !service || !desc) {
            errorBox.textContent = "Please fill in all required fields marked with *.";
            errorBox.style.display = 'block';
            successBox.style.display = 'none';
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            errorBox.textContent = "Please enter a valid email address.";
            errorBox.style.display = 'block';
            successBox.style.display = 'none';
            return;
        }

        // 2. Success State
        errorBox.style.display = 'none';
        successBox.textContent = "✅ Draft created! Opening your email client...";
        successBox.style.display = 'block';

        // 3. Build the email draft
        const subject = encodeURIComponent(`Security Assessment Request: ${service}`);
        const body = encodeURIComponent(
            `Name: ${name}\n` +
            `Company: ${company || 'N/A'}\n` +
            `Email: ${email}\n` +
            `Service Requested: ${service}\n\n` +
            `Project Description:\n${desc}`
        );

        const mailtoLink = `mailto:info@imvulalabs.co.za?subject=${subject}&body=${body}`;
        
        // 4. Open Email Client
        setTimeout(() => {
            window.location.href = mailtoLink;
            // Reset success message after opening
            setTimeout(() => { successBox.style.display = 'none'; }, 3000);
        }, 500);
    });
});