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

        // Show result section
        document.getElementById('result-message').textContent = result.message;
        document.getElementById('result-section').classList.remove('hidden');
        document.getElementById('loading-section').classList.add('hidden');

    } catch (error) {
        console.error('Error uploading file:', error);
        showError('An error occurred while uploading the file. Please try again.');
    }
}

