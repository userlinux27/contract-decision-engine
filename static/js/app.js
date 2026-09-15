// Initialize
const WorkmaticTemplates = window.WorkmaticTemplates || {};

document.addEventListener('DOMContentLoaded', () => {
    // Generate visitor ID
    if (!localStorage.getItem('visitor_id')) {
        localStorage.setItem('visitor_id', 'visitor_' + Math.random().toString(36).substr(2, 9));
    }

    // Retrieve template source for attribution (from template page CTA click)
    const templateSource = WorkmaticTemplates.getTemplateSource ? WorkmaticTemplates.getTemplateSource() : null;
    if (templateSource) {
        console.log('[Attribution] Template source:', templateSource);
        // Store for use during analysis
        window.templateAttribution = templateSource;
    }

    // File input handler
    document.getElementById('file-input').addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // Drag and drop
    const dropArea = document.getElementById('drop-area');
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    dropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });
});

// UI functions
function showLoading(message) {
    document.getElementById('loading-message').textContent = message;
    document.getElementById('loading-section').classList.remove('hidden');
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('result-section').classList.add('hidden');
    document.getElementById('error-section').classList.add('hidden');
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-section').classList.remove('hidden');
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('result-section').classList.add('hidden');
}

function showMain() {
    document.getElementById('upload-section').classList.remove('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('error-section').classList.add('hidden');
    document.getElementById('result-section').classList.add('hidden');
}

// ========== DEMO FLOW ==========

async function uploadFile(file) {
    try {
        console.log('Uploading:', file.name, file.size);

        // Use new API endpoint
        const formData = new FormData();
        formData.append('file', file);

        // Include template attribution if available
        if (window.templateAttribution) {
            formData.append('template_slug', window.templateAttribution.template_slug);
            formData.append('cta_location', window.templateAttribution.cta_location || 'unknown');
            formData.append('template_page_url', window.templateAttribution.page_url);
            formData.append('template_referrer', window.templateAttribution.referrer);
            formData.append('template_timestamp', window.templateAttribution.timestamp);
        }

        const resp = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!resp.ok) {
            throw new Error(`HTTP error! status: ${resp.status}`);
        }

        const result = await resp.json();
        console.log('Result:', result);

        if (!result.task_id) {
            showError('Server response missing task_id');
            return;
        }
        showLoading('Analyzing your contract…');
        await pollTask(result.task_id);

    } catch (error) {
        console.error('Error uploading file:', error);
        showError('An error occurred while uploading the file. Please try again.');
    }
}

// ========== POLLING & RESULT DISPLAY ==========

function showResult() {
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('error-section').classList.add('hidden');
    document.getElementById('result-section').classList.remove('hidden');
}

function updateTrafficLight(decision) {
    document.getElementById('traffic-light-safe').classList.remove('active');
    document.getElementById('traffic-light-changes').classList.remove('active');
    document.getElementById('traffic-light-reject').classList.remove('active');

    const decisionLabels = {
        'safe_to_sign': 'Ready to Sign',
        'sign_after_changes': 'Review Recommended',
        'do_not_sign': 'High Risk — Do Not Sign'
    };

    if (decision === 'safe_to_sign') {
        document.getElementById('traffic-light-safe').classList.add('active');
    } else if (decision === 'sign_after_changes') {
        document.getElementById('traffic-light-changes').classList.add('active');
    } else if (decision === 'do_not_sign') {
        document.getElementById('traffic-light-reject').classList.add('active');
    }

    document.getElementById('decision-text').textContent = decisionLabels[decision] || decision;
}

function populateFindings(findings) {
    const list = document.getElementById('findings-list');
    if (!list) return;
    list.innerHTML = '';

    if (!findings || findings.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No significant findings.';
        list.appendChild(li);
        return;
    }

    findings.forEach(f => {
        const li = document.createElement('li');
        li.className = `finding severity-${f.severity || 'low'}`;

        const clause = f.clause ? `Clause ${f.clause}: ` : '';
        const reason = f.llm_reason || f.reason || 'No reason provided';
        const impact = f.llm_impact || f.impact || '';
        const suggestedRewrite = f.llm_suggested_rewrite || f.suggested_rewrite || '';

        li.innerHTML = `
            <div class="finding-header">
                <span class="finding-type">${f.type || 'Unknown'}</span>
                <span class="finding-confidence">${Math.round((f.confidence || 0) * 100)}%</span>
            </div>
            <div class="finding-reason">${clause}${reason}</div>
            ${impact ? `<div class="finding-impact">${impact}</div>` : ''}
            ${suggestedRewrite ? `
            <div class="suggested-rewrite">
                <div class="rewrite-header">Suggested wording:</div>
                <div class="rewrite-text">${suggestedRewrite}</div>
                <button class="copy-btn" onclick="navigator.clipboard.writeText('${suggestedRewrite.replace(/'/g, "\\'")}')">Copy</button>
            </div>` : ''}
        `;
        list.appendChild(li);
    });
}

function populateAreasChecked(data) {
    const list = document.getElementById('areas-checked-list');
    if (!list) return;
    list.innerHTML = '';

    const findings = data.decision_details?.all_findings || [];
    const factors = new Set();

    findings.forEach(f => {
        if (f.type) factors.add(f.type);
    });

    const topReasons = data.decision_details?.top_reasons || [];
    topReasons.forEach(r => {
        if (r.factor) factors.add(r.factor);
    });

    if (factors.size === 0) {
        const li = document.createElement('li');
        li.textContent = 'Standard contract review completed.';
        list.appendChild(li);
        return;
    }

    factors.forEach(factor => {
        const li = document.createElement('li');
        li.textContent = factor;
        list.appendChild(li);
    });
}

function showRelevantTemplate(data) {
    const docType = data.classification?.display_name || '';
    const templateMap = {
        'Service Agreement': { slug: 'consulting-agreement', title: 'Consulting Agreement' },
        'Independent Contractor Agreement': { slug: 'independent-contractor-agreement', title: 'Independent Contractor Agreement' },
        'Freelance Agreement': { slug: 'freelance-agreement', title: 'Freelance Agreement' },
        'Master Services Agreement': { slug: 'master-services-agreement-msa', title: 'Master Services Agreement (MSA)' },
        'Non-Disclosure Agreement': { slug: 'non-disclosure-agreement-nda', title: 'Non-Disclosure Agreement (NDA)' }
    };

    const template = templateMap[docType];
    const el = document.getElementById('relevant-template');
    if (!el || !template) return;

    document.getElementById('template-suggestion-text').textContent =
        `Based on your ${docType.toLowerCase()}, you might find this template useful:`;
    document.getElementById('template-suggestion-link').href = `/templates/${template.slug}`;
    document.getElementById('template-suggestion-link').textContent = `View ${template.title} Template`;
    el.classList.remove('hidden');
}

function showToolResult(data) {
    if (!data || !data.classification || !data.pipeline) {
        console.error('Invalid analysis result:', data);
        showError('Analysis returned an incomplete result.');
        return;
    }

    const decision = data.decision;
    const confidence = data.decision_details?.confidence || 0;
    const confidencePercent = Math.round(confidence * 100);

    updateTrafficLight(decision);
    document.getElementById('confidence-text').textContent = `${confidencePercent}% confidence`;

    const classification = data.classification;
    document.getElementById('document-type').textContent = classification.display_name || 'Unknown';
    document.getElementById('classification-confidence').textContent = `${Math.round((classification.confidence || 0) * 100)}%`;
    document.getElementById('supported-status').textContent = classification.supported ? 'Yes' : 'No';

    const pipeline = data.pipeline;
    document.getElementById('pages-count').textContent = pipeline.pages || 'N/A';
    document.getElementById('reading-time').textContent = `${pipeline.estimated_reading_time_min || 0} min`;
    document.getElementById('language-detected').textContent = pipeline.language || 'en';

    populateFindings(data.decision_details?.all_findings || []);
    populateAreasChecked(data);
    showRelevantTemplate(data);
    showResult();
}

async function pollTask(taskId) {
    const maxAttempts = 60;
    const pollInterval = 1000;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            const statusMessages = [
                'Analyzing your contract…',
                'Reading document…',
                'Classifying document…',
                'Checking key terms…',
                'Preparing decision…'
            ];
            showLoading(statusMessages[attempt % statusMessages.length]);

            const resp = await fetch(`/api/tasks/${taskId}`);
            const data = await resp.json();
            console.log(`Poll attempt ${attempt + 1}:`, data.status);

            if (!resp.ok) {
                const errorMsg = data.error || data.detail || `Failed to check analysis status: ${resp.status}`;
                showError(errorMsg);
                return;
            }

            if (data.status === 'completed') {
                if (data.result) {
                    showToolResult(data.result);
                } else {
                    showError('Analysis completed but no result returned');
                }
                return;
            }

            if (data.status === 'failed') {
                const errorMsg = data.error || 'Analysis failed';
                showError(`Analysis failed: ${errorMsg}`);
                return;
            }

            if (attempt < maxAttempts - 1) {
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            }

        } catch (err) {
            console.error('Polling error:', err);
            showError(`Failed to check analysis status: ${err.message}`);
            return;
        }
    }

    showError('Analysis is taking longer than expected. Please try again.');
}

