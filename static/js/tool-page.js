// Tool Page JavaScript
// Handles upload, analysis, and result display for Free Contract Risk Checker

(function() {
    'use strict';

    const TOOL_SLUG = 'contract-risk-checker';

    // Track event function
    function trackEvent(eventName, properties = {}) {
        const payload = {
            event: eventName,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            referrer: document.referrer,
            tool_slug: TOOL_SLUG,
            ...properties
        };

        // Send to analytics endpoint
        fetch('/analytics/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            keepalive: true
        }).catch(() => {}); // Fail silently

        // Also log to console in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('[Analytics]', eventName, properties);
        }
    }

    // Store tool source for attribution
    function storeToolSource() {
        const sourceData = {
            tool_slug: TOOL_SLUG,
            timestamp: Date.now(),
            page_url: window.location.href,
            referrer: document.referrer,
            utm_source: new URLSearchParams(window.location.search).get('utm_source'),
            utm_medium: new URLSearchParams(window.location.search).get('utm_medium'),
            utm_campaign: new URLSearchParams(window.location.search).get('utm_campaign')
        };
        try {
            sessionStorage.setItem('workmatic_tool_source', JSON.stringify(sourceData));
            localStorage.setItem('workmatic_tool_source', JSON.stringify(sourceData));
        } catch (e) {}
    }

    // Retrieve tool source
    function getToolSource() {
        try {
            const session = sessionStorage.getItem('workmatic_tool_source');
            if (session) return JSON.parse(session);
            const local = localStorage.getItem('workmatic_tool_source');
            if (local) return JSON.parse(local);
        } catch (e) {}
        return null;
    }

    // Clear tool source
    function clearToolSource() {
        try {
            sessionStorage.removeItem('workmatic_tool_source');
            localStorage.removeItem('workmatic_tool_source');
        } catch (e) {}
    }

    // UI functions
    function showUpload() {
        document.getElementById('upload-section').classList.remove('hidden');
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('error-section').classList.add('hidden');
        document.getElementById('result-section').classList.add('hidden');
    }

    function showLoading(message) {
        document.getElementById('loading-message').textContent = message;
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('loading-section').classList.remove('hidden');
        document.getElementById('error-section').classList.add('hidden');
        document.getElementById('result-section').classList.add('hidden');
    }

    function showError(message) {
        document.getElementById('error-message').textContent = message;
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('error-section').classList.remove('hidden');
        document.getElementById('result-section').classList.add('hidden');
    }

    function showResult() {
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('error-section').classList.add('hidden');
        document.getElementById('result-section').classList.remove('hidden');

        // Scroll to result
        setTimeout(() => {
            document.getElementById('result-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 100);
    }

    function resetTool() {
        clearToolSource();
        document.getElementById('file-input').value = '';
        showUpload();
    }

    // Map decision to traffic light
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

    // Populate findings
    function populateFindings(findings) {
        const list = document.getElementById('findings-list');
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

    // Populate areas checked
    function populateAreasChecked(data) {
        const list = document.getElementById('areas-checked-list');
        list.innerHTML = '';

        // Extract unique factors/types from findings
        const findings = data.decision_details?.all_findings || [];
        const factors = new Set();

        findings.forEach(f => {
            if (f.type) factors.add(f.type);
        });

        // Also add from top_reasons
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

    // Show relevant template suggestion based on document type
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
        if (template) {
            document.getElementById('template-suggestion-text').textContent =
                `Based on your ${docType.toLowerCase()}, you might find this template useful:`;
            document.getElementById('template-suggestion-link').href = `/templates/${template.slug}`;
            document.getElementById('template-suggestion-link').textContent = `View ${template.title} Template`;
            document.getElementById('relevant-template').classList.remove('hidden');
        }
    }

    // Upload and analyze
    async function uploadFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please upload a PDF file.');
            return;
        }

        showLoading('Uploading…');
        trackEvent('tool_upload_started', { file_name: file.name, file_size: file.size });

        const formData = new FormData();
        formData.append('file', file);

        // Include tool attribution
        const toolSource = getToolSource();
        if (toolSource) {
            formData.append('tool_slug', toolSource.tool_slug);
            formData.append('tool_page_url', toolSource.page_url);
            formData.append('tool_referrer', toolSource.referrer);
            formData.append('tool_utm_source', toolSource.utm_source || '');
            formData.append('tool_utm_medium', toolSource.utm_medium || '');
            formData.append('tool_utm_campaign', toolSource.utm_campaign || '');
            formData.append('tool_timestamp', toolSource.timestamp);
        }

        try {
            console.log('Uploading:', file.name, file.size);

            const resp = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await resp.json();
            console.log('Upload response:', data);

            if (!resp.ok) {
                const errorMsg = data.error || data.detail || `Server error: ${resp.status}`;
                showError(errorMsg);
                return;
            }

            trackEvent('tool_upload_completed', { task_id: data.task_id });

            // Start task polling
            await pollTask(data.task_id);

        } catch (err) {
            console.error('Network/fetch error:', err);
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                showError('Network error. Please check your connection.');
            } else {
                showError(`Upload error: ${err.message}`);
            }
        }
    }

    // Task polling
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

    // Show tool result
    function showToolResult(data) {
        if (!data || !data.classification || !data.pipeline) {
            console.error('Invalid analysis result:', data);
            showError('Analysis returned an incomplete result.');
            return;
        }

        const decision = data.decision;
        const confidence = data.decision_details?.confidence || 0;
        const confidencePercent = Math.round(confidence * 100);

        // Update traffic light
        updateTrafficLight(decision);
        document.getElementById('confidence-text').textContent = `${confidencePercent}% confidence`;

        // Update classification
        const classification = data.classification;
        document.getElementById('document-type').textContent = classification.display_name || 'Unknown';
        document.getElementById('classification-confidence').textContent = `${Math.round((classification.confidence || 0) * 100)}%`;
        document.getElementById('supported-status').textContent = classification.supported ? 'Yes' : 'No';

        // Update pipeline info
        const pipeline = data.pipeline;
        document.getElementById('pages-count').textContent = pipeline.pages || 'N/A';
        document.getElementById('reading-time').textContent = `${pipeline.estimated_reading_time_min || 0} sec`;
        document.getElementById('language-detected').textContent = pipeline.language || 'en';

        // Populate findings
        const findings = data.decision_details?.all_findings || [];
        populateFindings(findings);

        // Populate areas checked
        populateAreasChecked(data);

        // Show relevant template suggestion
        showRelevantTemplate(data);

        // Track completion
        trackEvent('tool_analysis_completed', {
            decision: decision,
            confidence: confidencePercent,
            document_type: classification.display_name
        });

        showResult();
    }

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        storeToolSource();
        trackEvent('tool_page_view');

        // File input handler
        document.getElementById('file-input').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadFile(e.target.files[0]);
            }
        });

        // Upload trigger button
        document.getElementById('upload-trigger').addEventListener('click', () => {
            document.getElementById('file-input').click();
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

        // Track CTA clicks
        document.querySelectorAll('[data-cta-location]').forEach(cta => {
            cta.addEventListener('click', function() {
                const location = this.dataset.ctaLocation;
                trackEvent('tool_cta_click', { cta_location: location });

                if (location === 'tool_template') {
                    trackEvent('tool_template_clicked');
                } else if (location === 'tool_another') {
                    trackEvent('tool_second_analysis_started');
                }
            });
        });
    });

    // Expose for potential use by other pages
    window.WorkmaticTool = {
        trackEvent,
        getToolSource,
        clearToolSource,
        TOOL_SLUG
    };
})();