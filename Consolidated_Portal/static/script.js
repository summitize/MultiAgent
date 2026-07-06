document.addEventListener('DOMContentLoaded', () => {
    // Navigation logic
    const navLinks = document.querySelectorAll('.nav-links li');
    const toolSections = document.querySelectorAll('.tool-section');
    const pageTitle = document.getElementById('page-title');
    const responseContainer = document.getElementById('response-container');
    const responseContent = document.getElementById('response-content');
    const loader = document.getElementById('loader');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Update title
            pageTitle.textContent = link.querySelector('span').textContent.trim();

            // Show relevant section
            const targetId = link.getAttribute('data-target');
            toolSections.forEach(section => {
                if (section.id === targetId) {
                    section.classList.add('active-section');
                } else {
                    section.classList.remove('active-section');
                }
            });

            // Reset response area with new placeholder layout
            responseContent.innerHTML = `
                <div class="placeholder-text">
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                    <span>Select an agent, fill the details, and run to see response output.</span>
                </div>
            `;
            
            // Remove any existing action bar
            const existingActions = responseContainer.querySelector('.output-actions');
            if (existingActions) existingActions.remove();
        });
    });

    // Form Submissions Wrapper Helper
    async function handleFormSubmit(e, endpoint) {
        e.preventDefault();
        
        // Show loading state
        loader.style.display = 'flex';
        responseContent.innerHTML = '';
        
        // Remove any existing action bar during loading
        const existingActions = responseContainer.querySelector('.output-actions');
        if (existingActions) existingActions.remove();
        
        const form = e.target;
        const submitBtnAttr = form.querySelector('button[type="submit"]');
        submitBtnAttr.disabled = true;
        
        try {
            let response;
            if (endpoint.includes('fetch_and_summarize_news')) {
                // News relies on GET, others on POST usually
                const category = form.querySelector('[name="category"]').value;
                response = await fetch(`/api/fetch_and_summarize_news?category=${category}`);
            } else {
                const formData = new FormData(form);
                response = await fetch(`/api/${endpoint}`, {
                    method: 'POST',
                    body: formData
                });
            }

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Server Error: ${errText}`);
            }

            const data = await response.json();
            
            // Render conditionally based on endpoint structure
            if (data.code) {
                responseContent.innerHTML = `<pre><code>${escapeHtml(data.code)}</code></pre>`;
            } else if (data.content) {
                responseContent.innerHTML = `<p>${formatText(data.content)}</p>`;
            } else if (data.summary && data.articles) {
                let html = `<p>${formatText(data.summary)}</p><hr style="border-color: rgba(255,255,255,0.06); margin: 1.5rem 0;"><h4>Sources:</h4><ul style="margin-top: 0.75rem; padding-left: 1.25rem; line-height: 1.8;">`;
                data.articles.forEach(art => {
                    html += `<li><a href="${art.url}" target="_blank">${escapeHtml(art.title)}</a> (${escapeHtml(art.source.name)})</li>`;
                });
                html += '</ul>';
                responseContent.innerHTML = html;
            } else if (data.response) {
                const text = data.response;
                if (text.includes('```')) {
                    responseContent.innerHTML = formatMarkdownCodeBlocks(text);
                } else {
                    responseContent.innerHTML = `<p>${formatText(text)}</p>`;
                }
            } else {
                responseContent.innerHTML = `<p>${formatText(JSON.stringify(data))}</p>`;
            }

            // Add action bar (Copy button)
            const textToCopy = data.code || data.content || data.response || data.summary || JSON.stringify(data);
            if (textToCopy) {
                const actionBar = document.createElement('div');
                actionBar.className = 'output-actions';
                
                const copyBtn = document.createElement('button');
                copyBtn.className = 'btn-secondary';
                copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                copyBtn.addEventListener('click', async () => {
                    try {
                        await navigator.clipboard.writeText(textToCopy);
                        copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                        setTimeout(() => {
                            copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                        }, 2000);
                    } catch (err) {
                        console.error('Failed to copy text: ', err);
                    }
                });

                actionBar.appendChild(copyBtn);
                responseContainer.appendChild(actionBar);
            }

        } catch (error) {
            console.error(error);
            responseContent.innerHTML = `<div style="color: #ef4444; padding: 15px; border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.08); border-radius: 0.75rem; font-weight: 500;">Error: ${error.message}</div>`;
        } finally {
            loader.style.display = 'none';
            submitBtnAttr.disabled = false;
        }
    }

    // Connect forms
    document.getElementById('form-code').addEventListener('submit', (e) => handleFormSubmit(e, 'generate_code'));
    document.getElementById('form-content').addEventListener('submit', (e) => handleFormSubmit(e, 'generate_content'));
    document.getElementById('form-legal').addEventListener('submit', (e) => handleFormSubmit(e, 'analyze_legal_text'));
    document.getElementById('form-news').addEventListener('submit', (e) => handleFormSubmit(e, 'fetch_and_summarize_news'));
    document.getElementById('form-proofread').addEventListener('submit', (e) => handleFormSubmit(e, 'proofread'));
    document.getElementById('form-summarizer').addEventListener('submit', (e) => handleFormSubmit(e, 'summarize'));
    document.getElementById('form-virtual').addEventListener('submit', (e) => handleFormSubmit(e, 'virtual_assistant'));
    document.getElementById('form-support').addEventListener('submit', (e) => handleFormSubmit(e, 'customer_support'));
    document.getElementById('form-ecom').addEventListener('submit', (e) => handleFormSubmit(e, 'ecommerce_recommender'));
    document.getElementById('form-symptom').addEventListener('submit', (e) => handleFormSubmit(e, 'medical_symptom_checker'));

    // Utility: format raw text to light HTML
    function formatText(text) {
        if (!text) return "";
        return escapeHtml(text).replace(/\n/g, '<br>');
    }

    // Helper to format basic markdown code blocks
    function formatMarkdownCodeBlocks(text) {
        if (!text) return "";
        const parts = text.split(/(```[\s\S]*?```)/g);
        return parts.map(part => {
            if (part.startsWith('```')) {
                const lines = part.split('\n');
                const lang = lines[0].replace('```', '').trim();
                const code = lines.slice(1, -1).join('\n');
                return `<pre><code class="language-${lang}">${escapeHtml(code)}</code></pre>`;
            } else {
                return `<p>${formatText(part)}</p>`;
            }
        }).join('');
    }

    // Utility: sanitize input to prevent XSS
    function escapeHtml(unsafe) {
        return (unsafe || "").toString()
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
