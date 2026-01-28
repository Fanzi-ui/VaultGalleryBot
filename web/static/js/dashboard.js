const dashboardDataEl = document.getElementById("dashboard-data");
const dashboardData = dashboardDataEl ? JSON.parse(dashboardDataEl.textContent) : {};
const images = dashboardData.images || [];

// Keep existing rating modal logic and other non-slideshow related code
const logoToggleBtn = document.getElementById("logo-toggle");
const hero = document.querySelector(".hero");
const ratingModal = document.getElementById("rating-modal");
const ratingTitle = document.getElementById("rating-title");
const ratingPreview = document.getElementById("rating-preview");
const ratingValue = document.getElementById("rating-value");
const ratingCaption = document.getElementById("rating-caption");
const ratingSubmit = document.getElementById("rating-submit");
const ratingCancel = document.getElementById("rating-cancel");
const ratingNote = document.getElementById("rating-note");

// --- Splide.js Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    const slideshowEl = document.getElementById('slideshow');
    if (!slideshowEl) {
        return;
    }

    if (images.length === 0) {
        slideshowEl.classList.add('is-empty');
        return;
    }

    if (typeof Splide === 'undefined') {
        console.warn('Splide library not loaded; slideshow disabled.');
        slideshowEl.classList.add('is-error');
        return;
    }

    {
        const splide = new Splide('#slideshow', {
            type: 'fade',
            rewind: true,
            autoplay: true,
            interval: 4000,
            pauseOnHover: true,
            pauseOnFocus: false,
            arrows: true,
            pagination: false,
            speed: 1200, // Slower speed for a smoother fade
            aspectRatio: 1 / 1, // Set aspect ratio for card view (square)
            lazyLoad: 'sequential',
            preloadPages: 1,
            keyboard: 'global',
        });

        splide.mount();

        // Hook up controls
        const shuffleToggle = document.getElementById('shuffle-toggle');
        const motionToggle = document.getElementById('motion-toggle');

        if (shuffleToggle) {
            shuffleToggle.addEventListener('click', function() {
                // Go to a random slide
                const randomIndex = Math.floor(Math.random() * splide.length);
                splide.go(randomIndex);
            });
        }

        if (motionToggle) {
            motionToggle.addEventListener('click', function() {
                if (splide.options.autoplay) {
                    splide.Components.Autoplay.pause();
                    splide.options.autoplay = false; // Manually update option to reflect state
                    motionToggle.textContent = 'RESUME MOTION';
                } else {
                    splide.Components.Autoplay.play();
                    splide.options.autoplay = true; // Manually update option to reflect state
                    motionToggle.textContent = 'PAUSE MOTION';
                }
            });
        }
    }
});

// Other existing JS (e.g., logo toggle, rating modal logic)

// Logo Toggle
if (logoToggleBtn && hero) {
  logoToggleBtn.addEventListener("click", () => {
    hero.classList.toggle("hidden");
    if (hero.classList.contains("hidden")) {
      logoToggleBtn.textContent = "SHOW LOGO";
    } else {
      logoToggleBtn.textContent = "HIDE LOGO";
    }
  });
}

// Rating Modal logic (assuming these functions are defined elsewhere or need to be moved here)
// Placeholder for rating modal logic - ensure existing functionality is preserved
// Example:
// ratingSubmit.addEventListener('click', () => { /* save rating */ });
// ratingCancel.addEventListener('click', () => { ratingModal.classList.remove('active'); });
// ... and any other event listeners for the rating modal
