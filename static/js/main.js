(function () {
    'use strict';

    var hamburger = document.getElementById('hamburger');
    var mobileNav = document.getElementById('mobileNav');
    var searchToggle = document.getElementById('searchToggle');
    var searchOverlay = document.getElementById('searchOverlay');
    var searchClose = document.getElementById('searchClose');
    var searchInput = document.getElementById('searchInput');

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

    // Hamburger
    if (hamburger && mobileNav) {
        hamburger.addEventListener('click', function () {
            var isOpen = mobileNav.classList.contains('open');
            if (isOpen) {
                closeMobileNav();
            } else {
                openMobileNav();
            }
        });
    }

    // Close mobile nav when a link is clicked
    if (mobileNav) {
        mobileNav.querySelectorAll('a, button').forEach(function (el) {
            el.addEventListener('click', function () {
                closeMobileNav();
            });
        });
    }

    // Close mobile nav on Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (mobileNav && mobileNav.classList.contains('open')) {
                closeMobileNav();
            }
            if (searchOverlay && searchOverlay.classList.contains('open')) {
                searchOverlay.classList.remove('open');
            }
        }
    });

    // Close mobile nav on backdrop click
    if (mobileNav) {
        mobileNav.addEventListener('click', function (e) {
            if (e.target === mobileNav) {
                closeMobileNav();
            }
        });
    }

    // Search toggle
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

    // Alert dismiss
    document.querySelectorAll('.alert-dismiss').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var alert = this.parentNode;
            alert.style.transition = 'opacity 200ms ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 200);
        });
    });

    // Auto-dismiss messages
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            if (!alert.parentNode) return;
            alert.style.transition = 'opacity 200ms ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 200);
        }, 5000);
    });

    // Intersection Observer for scroll-triggered animations
    if ('IntersectionObserver' in window) {
        var animatingElements = document.querySelectorAll('.animate-in');
        if (animatingElements.length) {
            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.style.animationPlayState = 'running';
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.15 });

            animatingElements.forEach(function (el) {
                el.style.animationPlayState = 'paused';
                observer.observe(el);
            });
        }
    } else {
        document.querySelectorAll('.animate-in').forEach(function (el) {
            el.style.opacity = '1';
        });
    }

    // Password visibility toggle
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

    // Form submit loading state
    document.querySelectorAll('.auth-form').forEach(function (form) {
        form.addEventListener('submit', function () {
            var btn = this.querySelector('.btn-primary[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Please wait...';
            }
        });
    });

})();
