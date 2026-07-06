// Global function to load API documentation
async function loadAPIDocs() {
    const apiListContainer = document.getElementById('api-list');
    const loader = document.createElement('div');
    loader.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" style="margin-right: 10px;"></i>Loading API documentation...';
    apiListContainer.innerHTML = '';
    apiListContainer.appendChild(loader);
    
    try {
        const response = await fetch('/api/endpoints');
        const data = await response.json();
        const endpoints = data.endpoints || [];
        
        let html = `
            <div class="endpoints-info" style="background: rgba(96, 165, 250, 0.1); border-left: 4px solid #60a5fa; padding: 15px; margin-bottom: 20px; border-radius: 6px;">
                <p style="margin: 0; color: #a0aec0;">Total Endpoints: <strong style="color: #60a5fa;">${endpoints.length}</strong></p>
            </div>
        `;
        
        endpoints.forEach((endpoint, idx) => {
            html += `
                <div class="api-endpoint-card" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 16px; margin-bottom: 16px; transition: all 0.3s ease;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #60a5fa; font-size: 16px;">${idx + 1}. ${endpoint.name}</h4>
                        <span style="background: ${endpoint.method === 'POST' ? '#f59e0b' : '#10b981'}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">${endpoint.method}</span>
                    </div>
                    <div style="color: #cbd5e0; font-size: 13px; font-family: 'Courier New', monospace; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; margin-bottom: 12px; word-break: break-all;">
                        ${endpoint.endpoint}
                    </div>
                    <p style="margin: 0 0 12px 0; color: #a0aec0; font-size: 14px;">${endpoint.description}</p>
                    <div style="background: rgba(0,0,0,0.1); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
                        <p style="margin: 0 0 8px 0; color: #60a5fa; font-size: 12px; font-weight: 600;">Model: <strong>${endpoint.model}</strong></p>
                        <div style="color: #a0aec0; font-size: 12px;">
            `;
            
            Object.entries(endpoint.params).forEach(([key, value]) => {
                html += `<div style="margin: 4px 0;"><strong>${key}</strong>: ${value}</div>`;
            });
            
            html += `
                        </div>
                    </div>
                </div>
            `;
        });
        
        apiListContainer.innerHTML = html;
    } catch (error) {
        apiListContainer.innerHTML = `
            <div style="color: #ef4444; padding: 15px; border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.08); border-radius: 0.75rem; font-weight: 500;">
                <i class="fa-solid fa-exclamation-circle" style="margin-right: 10px;"></i>
                Error loading API documentation: ${error.message}
            </div>
        `;
    }
}

// Load API docs on page load if api-docs section is visible
window.addEventListener('load', () => {
    const apiDocLink = document.querySelector('[data-target="api-docs"]');
    if (apiDocLink) {
        apiDocLink.addEventListener('click', () => {
            setTimeout(() => loadAPIDocs(), 300);
        });
    }
});
