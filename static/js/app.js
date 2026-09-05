// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Generate visitor ID
    if (!localStorage.getItem('visitor_id')) {
        localStorage.setItem('visitor_id', 'visitor_' + Math.random().toString(36).substr(2, 9));
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
// Demo loader - SYNCHRONOUS, no polling
async function loadDemo(type) {
    showLoading('Loading demo…');
    
    try {
        const resp = await fetch(`/analyze/${type}`);
        if (!resp.ok) {
            throw new Error(`Demo failed: ${resp.status}`);
        }
        const data = await resp.json();
        
        // Hide loading immediately
        document.getElementById('loading-section').classList.add('hidden');
        
        // Show demo result directly
        showDemoResult(data, type);
    } catch (err) {
        console.error('Demo error:', err);
        showError(`Demo failed: ${err.message}`);
    }
}

// Show demo result - separate from pipeline result
function showDemoResult(data, type) {
    // Clear any previous results
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('result-section').classList.remove('hidden');
    
    // Update traffic light based on demo type
    document.getElementById('traffic-light-safe').classList.remove('active');
    document.getElementById('traffic-light-changes').classList.remove('active');
    document.getElementById('traffic-light-reject').classList.remove('active');
    
    // Map demo type to traffic light
    const decisionMap = {
        'safe': 'safe_to_sign',
        'changes': 'sign_after_changes', 
        'reject': 'do_not_sign'
    };
    
    const decision = decisionMap[type] || 'safe_to_sign';
    
    // Update traffic light
    if (decision === 'safe_to_sign') {
        document.getElementById('traffic-light-safe').classList.add('active');
        document.getElementById('decision-text').textContent = '✅ Ready to Sign';
    } else if (decision === 'sign_after_changes') {
        document.getElementById('traffic-light-changes').classList.add('active');
        document.getElementById('decision-text').textContent = '🟡 Review Recommended';
    } else if (decision === 'do_not_sign') {
        document.getElementById('traffic-light-reject').classList.add('active');
        document.getElementById('decision-text').textContent = '🔴 High Risk';
    }
    
    // Update confidence
    const confidence = data.confidence || 0.93;
    document.getElementById('confidence-text').textContent = `${Math.round(confidence * 100)}% confidence`;
    
    // Update document info for demo
    document.getElementById('document-type').textContent = 'Service Agreement';
    document.getElementById('classification-confidence').textContent = '95%';
    document.getElementById('supported-status').textContent = 'Yes';
    document.getElementById('pages-count').textContent = '5';
    document.getElementById('reading-time').textContent = '10 min';
    document.getElementById('language-detected').textContent = 'English';
    
    // Update findings list
    const findingsList = document.getElementById('findings-list');
    findingsList.innerHTML = '';
    
    if (data.top_reasons && data.top_reasons.length > 0) {
        data.top_reasons.forEach(reason => {
            const li = document.createElement('li');
            li.textContent = `${reason.factor || 'Unknown'}: ${reason.reason || ''}`;
            findingsList.appendChild(li);
        });
    } else {
        // Default demo findings
        const defaultFindings = [
            'Clear payment terms with reasonable deadlines',
            'Standard liability limitations',
            'Fair termination clauses',
            'No hidden fees or penalties'
        ];
        
        defaultFindings.forEach(finding => {
            const li = document.createElement('li');
            li.textContent = finding;
            findingsList.appendChild(li);
        });
    }
    
    // Update top reasons
    const reasonsList = document.getElementById('top-reasons-list');
    reasonsList.innerHTML = '';
    
    if (data.top_reasons && data.top_reasons.length > 0) {
        data.top_reasons.slice(0, 3).forEach(reason => {
            const li = document.createElement('li');
            li.textContent = `${reason.factor || 'Unknown'}: ${reason.reason || ''}`;
            reasonsList.appendChild(li);
        });
    }
    
    // Automatic scroll to result section
    setTimeout(() => {
        document.getElementById('result-section').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
}

// ========== REAL PDF FLOW ==========
// File upload with new API
async function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please upload a PDF file.');
        return;
    }

    showLoading('Uploading…');
    window.uploadStartTime = Date.now();

    const formData = new FormData();
    formData.append('file', file);

    try {
        console.log('Uploading:', file.name, file.size);

        // Use new API endpoint
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await resp.json();
        console.log('Upload response:', data);

        if (!resp.ok) {
            // HTTP error (400, 404, 500, etc.)
            const errorMsg = data.error || data.detail || `Server error: ${resp.status}`;
            showError(errorMsg);
            return;
        }

        // Check that we got task_id
        if (data.task_id && data.status === 'processing') {
            // Start task polling
            await pollTask(data.task_id);
        } else {
            // Unexpected response
            console.error('Unexpected response:', data);
            showError('Unexpected server response');
        }

    } catch (err) {
        console.error('Network/fetch error:', err);
        // Only real network errors show as Network error
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            showError('Network error. Please check your connection.');
        } else {
            showError(`Upload error: ${err.message}`);
        }
    }
}

// Task polling function
async function pollTask(taskId) {
    const maxAttempts = 60; // 60 attempts × 1 second = 1 minute
    const pollInterval = 1000; // 1 second

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            // Update status message
            const statusMessages = [
                'Analyzing your contract…',
                'Reading document…',
                'Classifying document…',
                'Checking key terms…',
                'Preparing decision…'
            ];
            const statusIndex = attempt % statusMessages.length;
            showLoading(statusMessages[statusIndex]);

            const resp = await fetch(`/api/tasks/${taskId}`);
            const data = await resp.json();
            console.log(`Poll attempt ${attempt + 1}:`, data.status);

            if (!resp.ok) {
                // HTTP error when checking status
                const errorMsg = data.error || data.detail || `Failed to check analysis status: ${resp.status}`;
                showError(errorMsg);
                return;
            }

            if (data.status === 'completed') {
                // Task completed successfully
                if (data.result) {
                    showPipelineResult(data.result);
                } else {
                    console.error('Completed task has no result:', data);
                    showError('Analysis completed but no result returned');
                }
                return;
            }

            if (data.status === 'failed') {
                // Task failed
                const errorMsg = data.error || 'Analysis failed';
                showError(`Analysis failed: ${errorMsg}`);
                return;
            }

            // Task still processing, wait and continue
            if (attempt < maxAttempts - 1) {
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            }

        } catch (err) {
            console.error('Polling error:', err);
            showError(`Failed to check analysis status: ${err.message}`);
            return;
        }
    }

    // Timeout exceeded
    showError('Analysis is taking longer than expected. Please try again.');
}

// Show pipeline result with defensive check
function showPipelineResult(data) {
    // Defensive check - make sure data is valid
    if (!data || !data.classification || !data.pipeline) {
        console.error('Invalid analysis result:', data);
        showError('Analysis returned an incomplete result.');
        return;
    }

    const decision = data.decision;
    const decisionLabels = data.decision_labels || {
        'safe_to_sign': '✅ Ready to Sign',
        'sign_after_changes': '🟡 Review Recommended', 
        'do_not_sign': '🔴 High Risk'
    };
    
    const label = decisionLabels[decision] || decision;
    const confidence = data.decision_details?.confidence || 0;
    const confidencePercent = Math.round(confidence * 100);
    
    // Update traffic light
    document.getElementById('traffic-light-safe').classList.remove('active');
    document.getElementById('traffic-light-changes').classList.remove('active');
    document.getElementById('traffic-light-reject').classList.remove('active');
    
    if (decision === 'safe_to_sign') {
        document.getElementById('traffic-light-safe').classList.add('active');
    } else if (decision === 'sign_after_changes') {
        document.getElementById('traffic-light-changes').classList.add('active');
    } else if (decision === 'do_not_sign') {
        document.getElementById('traffic-light-reject').classList.add('active');
    }
    
    // Update decision text
    document.getElementById('decision-text').textContent = label;
    document.getElementById('confidence-text').textContent = `${confidencePercent}% confidence`;
    
    // Update classification
    const classification = data.classification;
    document.getElementById('document-type').textContent = classification.display_name || 'Unknown';
    document.getElementById('classification-confidence').textContent = `${Math.round((classification.confidence || 0) * 100)}%`;
    document.getElementById('supported-status').textContent = classification.supported ? 'Yes' : 'No';
    
    // Update pipeline info
    const pipeline = data.pipeline;
    document.getElementById('pages-count').textContent = pipeline.pages || 'N/A';
    document.getElementById('reading-time').textContent = `${pipeline.estimated_reading_time_min || 0} min`;
    document.getElementById('language-detected').textContent = pipeline.language || 'en';
    
    // Update findings
    const findings = data.decision_details?.all_findings || [];
    const findingsList = document.getElementById('findings-list');
    findingsList.innerHTML = '';
    
    findings.forEach(f => {
        const li = document.createElement('li');
        li.className = `finding severity-${f.severity || 'low'}`;
        
        const clause = f.clause ? `Clause ${f.clause}: ` : '';
        const hasRewrite = f.suggested_rewrite ? 'has-rewrite' : '';
        
        li.innerHTML = `
            <div class="finding-header">
                <span class="finding-type">${f.type || 'Unknown'}</span>
                <span class="finding-confidence">${Math.round((f.confidence || 0) * 100)}%</span>
            </div>
            <div class="finding-reason">${clause}${f.reason || 'No reason provided'}</div>
            ${f.suggested_rewrite ? `
            <div class="suggested-rewrite">
                <div class="rewrite-header">Suggested wording:</div>
                <div class="rewrite-text">${f.suggested_rewrite}</div>
                <button class="copy-btn" onclick="navigator.clipboard.writeText('${f.suggested_rewrite.replace(/'/g, "\\'")}')">Copy</button>
            </div>` : ''}
        `;
        findingsList.appendChild(li);
    });
    
    // Update top reasons
    const topReasons = data.decision_details?.top_reasons || [];
    const reasonsList = document.getElementById('top-reasons-list');
    reasonsList.innerHTML = '';
    
    topReasons.forEach(r => {
        const li = document.createElement('li');
        li.textContent = `${r.factor || 'Unknown'}: ${r.reason || ''}`;
        reasonsList.appendChild(li);
    });
    
    // Show result section and hide loading
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('result-section').classList.remove('hidden');
    
    // Automatic scroll to result section
    setTimeout(() => {
        document.getElementById('result-section').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
    
    // Log event
    fetch('/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            visitor_id: localStorage.getItem('visitor_id') || 'unknown',
            action: 'deciding',
            time_to_decision: Math.round((Date.now() - window.uploadStartTime) / 1000)
        })
    }).catch(() => {});
}