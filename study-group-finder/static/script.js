document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("js-ready");

    const animatedBlocks = document.querySelectorAll(".fade-in, .app-card, .timeline-item, .hero-card, .auth-panel, .empty-state");

    animatedBlocks.forEach((block, index) => {
        block.style.animationDelay = `${Math.min(index * 70, 280)}ms`;
    });

    const loadingForms = document.querySelectorAll("form.js-loading-form");
    loadingForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const submitButton = event.submitter || form.querySelector("button[type='submit']");
            if (!submitButton) {
                return;
            }

            if (submitButton.dataset.loadingActive === "true") {
                event.preventDefault();
                return;
            }

            submitButton.dataset.loadingActive = "true";
            submitButton.dataset.originalLabel = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.classList.add("is-loading");
            submitButton.innerHTML = submitButton.dataset.loadingLabel || "Processing...";
        });
    });

    const copyButtons = document.querySelectorAll(".copy-invite-btn");
    copyButtons.forEach((button) => {
        button.addEventListener("click", async () => {
            const copyText = button.dataset.copyText;
            if (!copyText) {
                return;
            }

            const originalText = button.textContent;
            try {
                await navigator.clipboard.writeText(copyText);
                button.textContent = "Copied";
            } catch (error) {
                button.textContent = "Copy failed";
            }

            window.setTimeout(() => {
                button.textContent = originalText;
            }, 1100);
        });
    });

    const chatScroll = document.querySelector("#chatScroll");
    if (chatScroll) {
        chatScroll.scrollTop = chatScroll.scrollHeight;
    }
});
