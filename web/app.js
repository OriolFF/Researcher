// ================================================
// Historical Researcher Web Client
// ================================================

const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const form = document.getElementById('research-form');
const submitBtn = document.getElementById('submit-btn');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');
const tier2Badge = document.getElementById('tier2-badge');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkSystemHealth();
    form.addEventListener('submit', handleSubmit);
});

// ================================================
// Health Check
// ================================================

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        // Update Tier 2 badge
        if (data.tier2_available) {
            tier2Badge.classList.add('active');
            tier2Badge.textContent = 'Tier 2: Available';
        } else {
            tier2Badge.textContent = 'Tier 2: Unavailable';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        tier2Badge.textContent = 'Tier 2: Unknown';
    }
}

// ================================================
// Form Submission
// ================================================

async function handleSubmit(event) {
    event.preventDefault();
    
    // Hide previous results/errors
    hideResults();
    hideError();
    
    // Show loading state
    setLoading(true);
    
    // Get form data
    const formData = new FormData(form);
    const depth = formData.get('depth');
    const query = formData.get('query');
    const format = formData.get('format');
    const provider = formData.get('provider');
    const citations = formData.get('citations');
    
    // Determine endpoint
    let endpoint = '/research';
    if (depth === 'basic') {
        endpoint = '/research/basic';
    } else if (depth === 'deep') {
        endpoint = '/research/deep';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                output_format: format,
                llm_provider: provider,
                citation_format: citations
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Research failed');
        }
        
        const data = await response.json();
        displayResults(data, format);
        
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

// ================================================
// Display Results
// ================================================

function displayResults(data, format) {
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Update tier indicator
    const tierIndicator = document.getElementById('result-tier');
    const tierUsed = data.tier_used || 'tier1';
    tierIndicator.textContent = tierUsed === 'tier1' ? '⚡ Tier 1' : '🎓 Tier 2';
    tierIndicator.className = `tier-indicator ${tierUsed}`;
    
    // Update confidence score
    const confidenceScore = document.getElementById('confidence-score');
    const confidence = data.confidence || 0.5;
    confidenceScore.textContent = `Confidence: ${(confidence * 100).toFixed(0)}%`;
    confidenceScore.className = 'confidence-score';
    if (confidence >= 0.8) {
        // High confidence - keep default (green)
    } else if (confidence >= 0.6) {
        confidenceScore.classList.add('medium');
    } else {
        confidenceScore.classList.add('low');
    }
    
    // Update execution time
    const executionTime = document.getElementById('execution-time');
    const timeMs = data.execution_time_ms || 0;
    executionTime.textContent = `⏱️ ${(timeMs / 1000).toFixed(2)}s`;
    
    // Display findings
    const findingsContent = document.getElementById('findings-content');
    if (format === 'json') {
        findingsContent.innerHTML = `<pre class="json-display">${syntaxHighlightJSON(data.findings)}</pre>`;
    } else {
        findingsContent.textContent = data.findings || 'No findings available';
    }
    
    // Display sources
    const sourcesList = document.getElementById('sources-list');
    const sourceCount = document.getElementById('source-count');
    const sources = data.sources || [];
    sourceCount.textContent = sources.length;
    
    sourcesList.innerHTML = sources.map((source, index) => `
        <div class="source-item">
            <h4>[${index + 1}] ${escapeHtml(source.title || 'Untitled')}</h4>
            <a href="${escapeHtml(source.url)}" target="_blank">${escapeHtml(source.url)}</a>
            ${source.accessed ? `<div class="source-meta">Accessed: ${escapeHtml(source.accessed)}</div>` : ''}
        </div>
    `).join('');
    
    // Display citations
    const citationsContent = document.getElementById('citations-content');
    const citations = data.citations || [];
    if (citations.length > 0) {
        citationsContent.textContent = citations.join('\n\n');
    } else {
        citationsContent.textContent = 'No citations available';
    }
}

// ================================================
// Utility Functions
// ================================================

function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');
    } else {
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
    }
}

function showError(message) {
    errorSection.style.display = 'block';
    document.getElementById('error-text').textContent = message;
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    errorSection.style.display = 'none';
}

function hideResults() {
    resultsSection.style.display = 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function syntaxHighlightJSON(data) {
    if (typeof data !== 'string') {
        data = JSON.stringify(data, null, 2);
    }
    
    return data.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key';
            } else {
                cls = 'json-string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return `<span class="${cls}">${match}</span>`;
    });
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        // Show success feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        btn.style.background = '#10b981';
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    }).catch(err => {
        showError('Failed to copy to clipboard');
    });
}

// ================================================
// Example Queries (for testing)
// ================================================

const exampleQueries = [
    "What weapons were used at the Battle of Waterloo?",
    "Describe daily life in a medieval castle",
    "What was the role of women during the Renaissance?",
    "Find primary sources about the American Revolution",
    "What caused the fall of the Roman Empire?"
];

// Add click handler for random example (if you add a button for it)
function loadRandomExample() {
    const query = exampleQueries[Math.floor(Math.random() * exampleQueries.length)];
    document.getElementById('query').value = query;
}
