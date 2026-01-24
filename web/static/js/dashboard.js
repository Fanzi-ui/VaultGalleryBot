const dashboardDataEl = document.getElementById("dashboard-data");
const dashboardData = dashboardDataEl ? JSON.parse(dashboardDataEl.textContent) : {};
const images = dashboardData.images || [];

const bgImages = [
  document.getElementById("bg-image-1"),
  document.getElementById("bg-image-2"),
  document.getElementById("bg-image-3"),
];
const toggleBtn = document.getElementById("motion-toggle");
const shuffleBtn = document.getElementById("shuffle-toggle");
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


