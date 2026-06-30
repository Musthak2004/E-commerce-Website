(function () {
    'use strict';

    /* ── DOM references ── */
    var hamburger = document.getElementById('hamburger');
    var mobileNav = document.getElementById('mobileNav');
    var searchToggle = document.getElementById('searchToggle');
    var searchOverlay = document.getElementById('searchOverlay');
    var searchClose = document.getElementById('searchClose');
    var searchInput = document.getElementById('searchInput');
    var header = document.querySelector('.site-header');

    /* ═══════════════════════════════════════════════
       MOBILE NAV
       ═══════════════════════════════════════════════ */

    function closeMobileNav() {
        if (!hamburger || !mobileNav) return;
        hamburger.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
        mobileNav.classList.remove('open');
        document.body.style.overflow = '';
    }

    function openMobileNav() {
        if (!hamburger || !mobileNav) return;
        hamburger.classList.add('active');
        hamburger.setAttribute('aria-expanded', 'true');
        mobileNav.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    if (hamburger && mobileNav) {
        hamburger.addEventListener('click', function () {
            mobileNav.classList.contains('open') ? closeMobileNav() : openMobileNav();
        });
    }

    if (mobileNav) {
        mobileNav.querySelectorAll('a, button').forEach(function (el) {
            el.addEventListener('click', closeMobileNav);
        });
    }

    /* ═══════════════════════════════════════════════
       KEYBOARD — Escape
       ═══════════════════════════════════════════════ */

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (mobileNav && mobileNav.classList.contains('open')) closeMobileNav();
            if (searchOverlay && searchOverlay.classList.contains('open')) {
                searchOverlay.classList.remove('open');
            }
        }
    });

    if (mobileNav) {
        mobileNav.addEventListener('click', function (e) {
            if (e.target === mobileNav) closeMobileNav();
        });
    }

    /* ═══════════════════════════════════════════════
       SEARCH OVERLAY
       ═══════════════════════════════════════════════ */

    if (searchToggle && searchOverlay) {
        searchToggle.addEventListener('click', function () {
            searchOverlay.classList.add('open');
            if (searchInput) {
                setTimeout(function () { searchInput.focus(); }, 100);
            }
        });
    }

    if (searchClose && searchOverlay) {
        searchClose.addEventListener('click', function () {
            searchOverlay.classList.remove('open');
        });
    }

    /* ═══════════════════════════════════════════════
       HEADER SCROLL EFFECT
       ═══════════════════════════════════════════════ */

    function updateHeaderOnScroll() {
        if (!header) return;
        header.classList.toggle('is-scrolled', window.scrollY > 40);
    }

    if (header) {
        window.addEventListener('scroll', updateHeaderOnScroll, { passive: true });
        updateHeaderOnScroll(); // initial check
    }

    /* ═══════════════════════════════════════════════
       BACK TO TOP
       ═══════════════════════════════════════════════ */

    var backToTop = document.getElementById('backToTop');

    function updateBackToTop() {
        if (!backToTop) return;
        backToTop.classList.toggle('is-visible', window.scrollY > 400);
    }

    if (backToTop) {
        window.addEventListener('scroll', updateBackToTop, { passive: true });
        backToTop.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    /* ═══════════════════════════════════════════════
       SCROLL-TRIGGERED ANIMATIONS
       Uses data-animate attribute for robustness.
       ═══════════════════════════════════════════════ */

    if ('IntersectionObserver' in window) {
        var revealObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        // Observe elements with data-animate attribute
        document.querySelectorAll('[data-animate]').forEach(function (el) {
            el.style.animationPlayState = 'paused';
            revealObserver.observe(el);
        });

        // Also observe legacy animation classes for backwards compat
        var legacySelector = '.anim-up:not(.hero *):not(.auth-page *):not(.form-page *):not(.error-page *), .anim-scale:not(.auth-page *):not(.form-page *):not(.error-page *), .anim-slideDown:not(.messages), .anim-fadein, .anim-pop';
        document.querySelectorAll(legacySelector).forEach(function (el) {
            // Only observe if not already using data-animate
            if (!el.hasAttribute('data-animate')) {
                el.style.animationPlayState = 'paused';
                revealObserver.observe(el);
            }
        });

        /* ── Section reveal (section-reveal) ── */
        var sectionObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    sectionObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.05 });

        document.querySelectorAll('.section-reveal').forEach(function (el) {
            sectionObserver.observe(el);
        });
    } else {
        // Fallback: make everything visible immediately
        document.querySelectorAll('[data-animate], .anim-up, .anim-scale, .anim-slideDown, .anim-fadein, .anim-pop, .section-reveal').forEach(function (el) {
            if (el.classList) el.classList.add('is-visible');
            el.style.opacity = '1';
        });
    }

    /* ═══════════════════════════════════════════════
       IMAGE BLUR-UP LAZY LOADING
       ═══════════════════════════════════════════════ */

    document.querySelectorAll('.img-blur-wrap img').forEach(function (img) {
        if (img.complete) {
            img.classList.add('loaded');
            img.closest('.img-blur-wrap') && img.closest('.img-blur-wrap').classList.add('loaded');
        } else {
            img.addEventListener('load', function () {
                img.classList.add('loaded');
                var wrap = img.closest('.img-blur-wrap');
                if (wrap) wrap.classList.add('loaded');
            });
            img.addEventListener('error', function () {
                img.classList.add('loaded'); // show broken image fallback regardless
                var wrap = img.closest('.img-blur-wrap');
                if (wrap) wrap.classList.add('loaded');
            });
        }
    });

    /* ═══════════════════════════════════════════════
       ALERT DISMISS
       ═══════════════════════════════════════════════ */

    document.querySelectorAll('.alert-dismiss').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var alert = this.parentNode;
            alert.style.transition = 'opacity 200ms ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) alert.remove();
            }, 200);
        });
    });

    // Auto-dismiss messages after 5 seconds
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            if (!alert.parentNode) return;
            alert.style.transition = 'opacity 200ms ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) alert.remove();
            }, 200);
        }, 5000);
    });

    /* ═══════════════════════════════════════════════
       TOAST NOTIFICATION SYSTEM
       ═══════════════════════════════════════════════ */

    function ensureToastContainer() {
        var container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            container.setAttribute('aria-live', 'polite');
            container.setAttribute('aria-relevant', 'additions');
            document.body.appendChild(container);
        }
        return container;
    }

    window.addToast = function (message, type) {
        type = type || 'info';
        var container = ensureToastContainer();
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.setAttribute('role', 'status');

        var icons = { success: 'check-circle', error: 'exclamation-circle', info: 'info-circle' };
        toast.innerHTML = '<i class="fas fa-' + (icons[type] || 'info-circle') + '"></i> ' + escapeHtml(message);

        container.appendChild(toast);

        // Remove after 4 seconds
        setTimeout(function () {
            toast.classList.add('is-dismissing');
            setTimeout(function () {
                if (toast.parentNode) toast.remove();
            }, 200);
        }, 4000);
    };

    /* ═══════════════════════════════════════════════
       PASSWORD VISIBILITY TOGGLE
       ═══════════════════════════════════════════════ */

    document.querySelectorAll('.pw-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = this.parentNode.querySelector('input');
            var icon = this.querySelector('i');
            if (input && icon) {
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.className = 'fas fa-eye-slash';
                } else {
                    input.type = 'password';
                    icon.className = 'fas fa-eye';
                }
            }
        });
    });

    /* ═══════════════════════════════════════════════
       FORM SUBMIT LOADING STATE
       ═══════════════════════════════════════════════ */

    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            var btn = this.querySelector('.btn-primary[type="submit"], .btn-submit[type="submit"], .btn-checkout[type="submit"]');
            if (btn && !btn.classList.contains('btn-loading')) {
                btn.classList.add('btn-loading');
                btn.disabled = true;
                var originalText = btn.innerHTML;
                btn.setAttribute('data-original-text', originalText);
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    });

    /* ═══════════════════════════════════════════════
       PROMPT ASSISTANT
       ═══════════════════════════════════════════════ */

    var promptAssistant = document.getElementById('promptAssistant');
    if (promptAssistant) {
        var suggestions = promptAssistant.querySelectorAll('.prompt-suggestion');
        var textarea = promptAssistant.querySelector('.prompt-input-wrap textarea');
        var sendBtn = promptAssistant.querySelector('.prompt-input-btn');
        var response = promptAssistant.querySelector('.prompt-response');

        suggestions.forEach(function (suggestion) {
            suggestion.addEventListener('click', function () {
                var text = this.getAttribute('data-prompt') || this.textContent.trim();
                if (textarea) {
                    textarea.value = text;
                    textarea.focus();
                    var evt = document.createEvent('Event');
                    evt.initEvent('input', true, true);
                    textarea.dispatchEvent(evt);
                }
                if (response) response.classList.remove('is-visible');
            });
        });

        if (sendBtn && textarea) {
            sendBtn.addEventListener('click', function () {
                var text = textarea.value.trim();
                if (!text) return;
                if (response) {
                    response.innerHTML = '<strong>You searched:</strong> ' + escapeHtml(text);
                    response.classList.add('is-visible');
                }
                textarea.value = '';
                sendBtn.disabled = true;
                textarea.focus();
            });

            textarea.addEventListener('input', function () {
                sendBtn.disabled = !this.value.trim();
            });
        }

        function escapeHtml(str) {
            var div = document.createElement('div');
            div.appendChild(document.createTextNode(str));
            return div.innerHTML;
        }
    }

})();
