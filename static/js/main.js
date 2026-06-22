(function () {
    'use strict';

    var hamburger = document.getElementById('hamburger');
    var mobileNav = document.getElementById('mobileNav');
    var searchToggle = document.getElementById('searchToggle');
    var searchOverlay = document.getElementById('searchOverlay');
    var searchClose = document.getElementById('searchClose');
    var searchInput = document.getElementById('searchInput');

    function closeMobileNav() {
        hamburger.classList.remove('active');
        mobileNav.classList.remove('open');
        document.body.style.overflow = '';
    }

    // Hamburger
    if (hamburger && mobileNav) {
        hamburger.addEventListener('click', function () {
            var isOpen = mobileNav.classList.contains('open');
            if (isOpen) {
                closeMobileNav();
            } else {
                hamburger.classList.add('active');
                mobileNav.classList.add('open');
                document.body.style.overflow = 'hidden';
            }
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

    // Search toggle
    if (searchToggle && searchOverlay) {
        searchToggle.addEventListener('click', function () {
            searchOverlay.classList.add('open');
            if (searchInput) {
                searchInput.focus();
            }
        });
    }

    if (searchClose && searchOverlay) {
        searchClose.addEventListener('click', function () {
            searchOverlay.classList.remove('open');
        });
    }

    // Auto-dismiss messages
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 200ms ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 200);
        }, 5000);
    });

})();
