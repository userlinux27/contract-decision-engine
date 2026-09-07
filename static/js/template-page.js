// Template Page JavaScript
// Handles download tracking, copy contract, and CTA attribution

(function() {
    'use strict';

    // Track event function
    function trackEvent(eventName, properties = {}) {
        const payload = {
            event: eventName,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            referrer: document.referrer,
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

    // Get template slug from page
    function getTemplateSlug() {
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn && downloadBtn.dataset.slug) {
            return downloadBtn.dataset.slug;
        }
        const copyBtn = document.getElementById('copy-btn');
        if (copyBtn && copyBtn.dataset.slug) {
            return copyBtn.dataset.slug;
        }
        // Fallback: extract from URL
        const match = window.location.pathname.match(/\/templates\/([^\/]+)/);
        return match ? match[1] : 'unknown';
    }

    // Store template source for attribution
    function storeTemplateSource(slug) {
        const sourceData = {
            template_slug: slug,
            timestamp: Date.now(),
            page_url: window.location.href,
            referrer: document.referrer
        };
        try {
            sessionStorage.setItem('workmatic_template_source', JSON.stringify(sourceData));
            localStorage.setItem('workmatic_template_source', JSON.stringify(sourceData));
        } catch (e) {}
    }

    // Retrieve template source
    function getTemplateSource() {
        try {
            const session = sessionStorage.getItem('workmatic_template_source');
            if (session) return JSON.parse(session);
            const local = localStorage.getItem('workmatic_template_source');
            if (local) return JSON.parse(local);
        } catch (e) {}
        return null;
    }

    // Clear template source (call after successful analysis)
    function clearTemplateSource() {
        try {
            sessionStorage.removeItem('workmatic_template_source');
            localStorage.removeItem('workmatic_template_source');
        } catch (e) {}
    }

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        const slug = getTemplateSlug();
        storeTemplateSource(slug);

        // Track page view
        trackEvent('template_page_view', {
            template_slug: slug,
            jurisdiction: document.querySelector('.template-badge')?.textContent || ''
        });

        // Download button tracking
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function(e) {
                trackEvent('template_download_click', {
                    template_slug: slug,
                    location: 'hero'
                });
                // Don't prevent default - let the download happen
            });
        }

        // Copy contract text
        const copyBtn = document.getElementById('copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', function() {
                const content = document.getElementById('contract-content');
                if (content) {
                    const text = content.innerText || content.textContent;
                    navigator.clipboard.writeText(text).then(() => {
                        trackEvent('template_copy_click', { template_slug: slug });
                        // Visual feedback
                        const originalText = copyBtn.innerHTML;
                        copyBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg><span>Copied!</span>';
                        copyBtn.classList.add('copied');
                        setTimeout(() => {
                            copyBtn.innerHTML = originalText;
                            copyBtn.classList.remove('copied');
                        }, 2000);
                    }).catch(() => {
                        // Fallback for older browsers
                        const textarea = document.createElement('textarea');
                        textarea.value = text;
                        document.body.appendChild(textarea);
                        textarea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textarea);
                        trackEvent('template_copy_click', { template_slug: slug });
                    });
                }
            });
        }

        // Track all CTA clicks with attribution
        document.querySelectorAll('[data-cta-location]').forEach(cta => {
            cta.addEventListener('click', function() {
                const location = this.dataset.ctaLocation;
                trackEvent('template_cta_click', {
                    template_slug: slug,
                    cta_location: location
                });
            });
        });

        // Track FAQ interactions
        document.querySelectorAll('.faq-item summary').forEach(summary => {
            summary.addEventListener('click', function() {
                const question = this.textContent.trim();
                trackEvent('template_faq_toggle', {
                    template_slug: slug,
                    question: question
                });
            });
        });

        // Track related template clicks
        document.querySelectorAll('.related-templates .template-card a').forEach(link => {
            link.addEventListener('click', function() {
                const relatedSlug = this.getAttribute('href').replace('/templates/', '');
                trackEvent('template_related_click', {
                    template_slug: slug,
                    related_slug: relatedSlug
                });
            });
        });
    });

    // Expose for use by analyze page
    window.WorkmaticTemplates = {
        trackEvent,
        getTemplateSource,
        clearTemplateSource,
        getTemplateSlug
    };
})();