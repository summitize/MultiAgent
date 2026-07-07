// ============================================================================
// MultiAgent AI Delivery Operating System - Dynamic Script
// ============================================================================

const logger = {
    info:  (msg, ...a) => console.log(`[INFO] ${msg}`, ...a),
    error: (msg, ...a) => console.error(`[ERROR] ${msg}`, ...a),
    debug: (msg, ...a) => console.debug(`[DEBUG] ${msg}`, ...a),
};

// Global state
let allAgents = [];
let currentAgent = null;

// Endpoint map: agent-id → unified API path via /api/agent/{agent_id}/invoke
const endpointMap = {
    // DeliveryOS AI Agents - all use unified endpoint
    'executive-copilot': '/api/agent/executive-copilot/invoke',
    'program-manager': '/api/agent/program-manager/invoke',
    'delivery-manager': '/api/agent/delivery-manager/invoke',
    'scrum-master': '/api/agent/scrum-master/invoke',
    'product-owner': '/api/agent/product-owner/invoke',
    'business-analyst': '/api/agent/business-analyst/invoke',
    'architect': '/api/agent/architect/invoke',
    'engineering-manager': '/api/agent/engineering-manager/invoke',
    'developer': '/api/agent/developer/invoke',
    'qa-engineer': '/api/agent/qa-engineer/invoke',
    'devops-engineer': '/api/agent/devops-engineer/invoke',
    'security-engineer': '/api/agent/security-engineer/invoke',
    'raid-manager': '/api/agent/raid-manager/invoke',
    'risk-prediction': '/api/agent/risk-prediction/invoke',
    'resource-manager': '/api/agent/resource-manager/invoke',
    'delivery-analytics': '/api/agent/delivery-analytics/invoke',
    'meeting-intelligence': '/api/agent/meeting-intelligence/invoke',
    'documentation-assistant': '/api/agent/documentation-assistant/invoke',
    'communication-assistant': '/api/agent/communication-assistant/invoke',
    'pmo': '/api/agent/pmo/invoke',
};

// ============================================================================
// LOAD AGENTS
// ============================================================================
async function loadAgents() {
    try {
        logger.info('Fetching agents...');
        const res = await fetch('/api/agents');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        allAgents = data.agents || [];
        logger.info(`Loaded ${allAgents.length} agents`);
        renderAgentNavigation();
        checkOllamaStatus();
        if (allAgents.length > 0) selectAgent(allAgents[0].id);
    } catch (err) {
        logger.error('Failed to load agents:', err);
        const nav = document.getElementById('agent-nav');
        if (nav) nav.innerHTML = `<li class="loading" style="color:#ef4444;">
            <i class="fa-solid fa-exclamation-circle"></i> Failed to load agents.<br><small>Is the server running on port 8000?</small></li>`;
    }
}

// ============================================================================
// RENDER NAVIGATION
// ============================================================================
function renderAgentNavigation() {
    const nav = document.getElementById('agent-nav');
    if (!nav) return;
    nav.innerHTML = '';
    allAgents.forEach(agent => {
        const li = document.createElement('li');
        li.setAttribute('data-agent-id', agent.id);
        li.innerHTML = `<i class="fa-solid ${agent.icon || 'fa-robot'}"></i><span>${agent.name}</span>`;
        li.addEventListener('click', () => selectAgent(agent.id));
        nav.appendChild(li);
    });
}

// ============================================================================
// SELECT AGENT
// ============================================================================
function selectAgent(agentId) {
    const agent = allAgents.find(a => a.id === agentId);
    if (!agent) return;
    currentAgent = agent;

    // Update nav active state
    document.querySelectorAll('#agent-nav li').forEach(li =>
        li.classList.toggle('active', li.getAttribute('data-agent-id') === agentId));

    // Update page title
    const pt = document.getElementById('page-title');
    if (pt) pt.textContent = agent.name;

    renderAgentDescription(agent);
    renderAgentForm(agent);

    // Clear response
    const rc = document.getElementById('response-content');
    if (rc) rc.innerHTML = `<div class="placeholder-text">
        <i class="fa-solid fa-wand-magic-sparkles"></i>
        <span>Fill in the details and submit to see ${agent.name}'s response.</span></div>`;
    document.querySelector('.output-actions')?.remove();
}

// ============================================================================
// RENDER DESCRIPTION
// ============================================================================
function renderAgentDescription(agent) {
    const container = document.getElementById('agent-description');
    if (!container) return;
    container.innerHTML = `
        <div class="agent-header">
            <div class="agent-icon-wrap"><i class="fa-solid ${agent.icon || 'fa-robot'}"></i></div>
            <div class="agent-meta">
                <h2>${escapeHtml(agent.name)}</h2>
                <p>${escapeHtml(agent.description || '')}</p>
                <div class="agent-badges">
                    <span class="badge badge-category">${escapeHtml(agent.category || 'general')}</span>
                    <span class="badge badge-model"><i class="fa-solid fa-microchip"></i> ${escapeHtml((agent.supportedModels && agent.supportedModels[0]) || agent.model || 'unknown')}</span>
                </div>
            </div>
        </div>`;
}

// ============================================================================
// RENDER FORM (explicit field map per agent)
// ============================================================================
function getAgentFields(agentId) {
    const map = {
        'code-assistant':    [{ name:'prompt',      label:'Code Request',       type:'textarea', ph:'Describe the code you need (e.g. Python sorting function)' }],
        'content-writer':    [{ name:'topic',        label:'Topic',              type:'textarea', ph:'What should the content be about?' }],
        'legal-analyzer':    [{ name:'text',         label:'Legal Document',     type:'textarea', ph:'Paste the legal text or contract here...' }],
        'news-summarizer':   [{ name:'category',     label:'News Category',      type:'select',   options:['technology','business','health','science','entertainment','sports'] }],
        'proofreader':       [{ name:'text',         label:'Text to Proofread',  type:'textarea', ph:'Paste your text here...' }],
        'text-summarizer':   [{ name:'text',         label:'Text to Summarize',  type:'textarea', ph:'Paste long text to summarize...' }],
        'virtual-assistant': [{ name:'user_query',   label:'Your Request',       type:'textarea', ph:'What do you need help with?' }],
        'customer-support':  [{ name:'user_query',   label:'Customer Issue',     type:'textarea', ph:'Describe the customer issue...' }],
        'shop-recommender':  [{ name:'preferences',  label:'Preferences',        type:'text',     ph:'E.g. Gaming laptop under $1000' }],
        'symptom-checker':   [{ name:'symptoms',     label:'Symptoms',           type:'textarea', ph:'Describe your symptoms in detail...' }],
    };
    return map[agentId] || [{ name:'prompt', label:'Input', type:'textarea', ph:'Enter your request...' }];
}

function renderAgentForm(agent) {
    const form = document.getElementById('dynamic-agent-form');
    if (!form) return;
    const fields = getAgentFields(agent.id);
    let html = '';
    fields.forEach(f => {
        html += `<div class="form-group"><label for="field-${f.name}">${escapeHtml(f.label)}</label>`;
        if (f.type === 'textarea') {
            html += `<textarea id="field-${f.name}" name="${f.name}" placeholder="${escapeHtml(f.ph||'')}" rows="5"></textarea>`;
        } else if (f.type === 'select') {
            html += `<select id="field-${f.name}" name="${f.name}">`;
            (f.options||[]).forEach(o => { html += `<option value="${escapeHtml(o)}">${escapeHtml(o[0].toUpperCase()+o.slice(1))}</option>`; });
            html += `</select>`;
        } else {
            html += `<input type="text" id="field-${f.name}" name="${f.name}" placeholder="${escapeHtml(f.ph||'')}">`;
        }
        html += `</div>`;
    });
    html += `<button type="submit" class="btn-primary"><i class="fa-solid fa-paper-plane"></i> Run ${escapeHtml(agent.name)}</button>`;
    form.innerHTML = html;
}

// ============================================================================
// SUBMIT HANDLER
// ============================================================================
async function handleAgentSubmit(e) {
    e.preventDefault();
    if (!currentAgent) return;

    const loader = document.getElementById('loader');
    const responseContent = document.getElementById('response-content');
    const responseContainer = document.getElementById('response-container');
    const submitBtn = e.target.querySelector('button[type="submit"]');

    if (loader) loader.style.display = 'flex';
    if (responseContent) responseContent.innerHTML = '';
    document.querySelector('.output-actions')?.remove();
    if (submitBtn) submitBtn.disabled = true;

    try {
        const formData = new FormData(e.target);
        const endpoint = endpointMap[currentAgent.id] || `/api/agent/${currentAgent.id}/invoke`;
        const res = await fetch(endpoint, { method:'POST', body:formData });
        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`Server ${res.status}: ${errText}`);
        }
        const responseData = await res.json();

        displayResponse(responseData);
    } catch (err) {
        logger.error('Agent failed:', err);
        if (responseContent) responseContent.innerHTML = `
            <div style="color:#ef4444;padding:15px;border-left:4px solid #ef4444;background:rgba(239,68,68,0.08);border-radius:0.75rem;">
                <i class="fa-solid fa-circle-exclamation"></i> ${escapeHtml(err.message)}</div>`;
    } finally {
        if (loader) loader.style.display = 'none';
        if (submitBtn) submitBtn.disabled = false;
    }
}

// ============================================================================
// DISPLAY RESPONSE
// ============================================================================
function displayResponse(data) {
    const responseContent = document.getElementById('response-content');
    const responseContainer = document.getElementById('response-container');
    if (!responseContent) return;

    let html = '', textToCopy = '';

    if (data.response) {
        textToCopy = data.response;
        html = data.response.includes('```') ? formatMarkdownCodeBlocks(data.response) : `<p>${formatText(data.response)}</p>`;
    } else if (data.summary && data.articles) {
        textToCopy = data.summary;
        html = `<p>${formatText(data.summary)}</p><hr style="border-color:rgba(255,255,255,0.06);margin:1.5rem 0;"><h4>Sources</h4><ul style="margin-top:0.75rem;padding-left:1.25rem;line-height:1.8;">`;
        (data.articles||[]).forEach(a => { html += `<li><a href="${escapeHtml(a.url||'#')}" target="_blank">${escapeHtml(a.title||'Article')}</a></li>`; });
        html += '</ul>';
    } else if (data.articles) {
        html = `<ul style="padding-left:1.25rem;line-height:1.8;">`;
        (data.articles||[]).forEach(a => { html += `<li><a href="${escapeHtml(a.url||'#')}" target="_blank">${escapeHtml(a.title||'Article')}</a></li>`; });
        html += '</ul>';
    } else if (data.error) {
        html = `<div style="color:#ef4444;padding:15px;border-left:4px solid #ef4444;background:rgba(239,68,68,0.08);border-radius:0.75rem;">
            <i class="fa-solid fa-circle-exclamation"></i> ${escapeHtml(data.error)}</div>`;
    } else {
        textToCopy = JSON.stringify(data, null, 2);
        html = `<pre style="white-space:pre-wrap;">${escapeHtml(textToCopy)}</pre>`;
    }

    responseContent.innerHTML = html;

    if (textToCopy && responseContainer) {
        const bar = document.createElement('div');
        bar.className = 'output-actions';
        const btn = document.createElement('button');
        btn.className = 'btn-secondary';
        btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
        btn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(textToCopy);
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy'; }, 2000);
            } catch(e) { logger.error('Copy failed',e); }
        });
        bar.appendChild(btn);
        responseContainer.appendChild(bar);
    }
}

// ============================================================================
// OLLAMA STATUS
// ============================================================================
async function checkOllamaStatus() {
    try {
        const res = await fetch('/api/ollama-status');
        const data = await res.json();
        data.available ? removeOllamaWarning() : showOllamaWarning(data.error || 'Ollama unavailable');
    } catch(e) { showOllamaWarning('Cannot reach server'); }
}

function showOllamaWarning(msg) {
    let b = document.getElementById('ollama-warning-banner');
    if (!b) {
        b = document.createElement('div');
        b.id = 'ollama-warning-banner';
        b.style.cssText = 'background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;padding:12px 20px;border-bottom:2px solid #991b1b;display:flex;align-items:center;justify-content:space-between;font-weight:500;position:sticky;top:0;z-index:100;';
        document.body.insertBefore(b, document.body.firstChild);
    }
    b.innerHTML = `<span><i class="fa-solid fa-exclamation-triangle"></i> Ollama unavailable: ${escapeHtml(msg)}</span>
        <button onclick="this.parentElement.remove()" style="background:rgba(255,255,255,0.2);border:none;color:#fff;padding:4px 10px;border-radius:4px;cursor:pointer;">✕</button>`;
}

function removeOllamaWarning() { document.getElementById('ollama-warning-banner')?.remove(); }

// ============================================================================
// UTILITIES
// ============================================================================
function escapeHtml(s) {
    return (s||'').toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}
function formatText(t) { return t ? escapeHtml(t).replace(/\n/g,'<br>') : ''; }
function formatMarkdownCodeBlocks(text) {
    if (!text) return '';
    return text.split(/(```[\s\S]*?```)/g).map(part => {
        if (part.startsWith('```')) {
            const lines = part.split('\n');
            const lang = lines[0].replace('```','').trim();
            const code = lines.slice(1,-1).join('\n');
            return `<pre><code class="language-${escapeHtml(lang)}">${escapeHtml(code)}</code></pre>`;
        }
        return part ? `<p>${formatText(part)}</p>` : '';
    }).join('');
}

// ============================================================================
// INIT
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    loadAgents();

    // Event delegation for the dynamic form (handles re-renders)
    document.body.addEventListener('submit', e => {
        if (e.target && e.target.id === 'dynamic-agent-form') handleAgentSubmit(e);
    });
});
