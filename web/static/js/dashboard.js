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

let paused = false;
let index = 0;
let currentRatedItem = null;

function pickImage() {
  if (!images.length) return null;
  const img = images[index];
  index = (index + 1) % images.length;
  return img;
}

function refreshBackgroundImages() {
  if (!images.length) return;
  const slots = [
    { left: "6%", top: "18%" },
    { left: "36%", top: "8%" },
    { left: "66%", top: "20%" },
  ];

  bgImages.forEach((img, i) => {
    const item = pickImage();
    if (!item || !item.url) return;
    img.classList.remove("is-loaded");
    img.src = item.url;
    img.dataset.mediaId = item.id;
    img.dataset.modelName = item.model_name || "";
    img.dataset.rating = item.rating ?? "";
    img.dataset.caption = item.rating_caption ?? "";
    img.style.left = slots[i].left;
    img.style.top = slots[i].top;
  });
}

toggleBtn.onclick = () => {
  paused = !paused;
  toggleBtn.textContent = paused ? "RESUME MOTION" : "PAUSE MOTION";
};

shuffleBtn.onclick = () => {
  window.location.reload();
};

logoToggleBtn.onclick = () => {
  const isHidden = hero.classList.toggle("hidden");
  logoToggleBtn.textContent = isHidden ? "SHOW LOGO" : "HIDE LOGO";
};

function openRatingModal(item) {
  currentRatedItem = item;
  const modelName = item.model_name || item.modelName || "Unknown";
  ratingTitle.textContent = `${modelName} • Rate Image`;
  ratingPreview.src = item.url;
  ratingValue.textContent = item.rating ? `${item.rating}/100` : "Unrated";
  const hasCaption = !!item.rating_caption;
  ratingCaption.value = item.rating_caption ?? "";
  ratingNote.textContent = item.rating ? "Auto-rated. Add a caption." : "Rating pending.";
  ratingCaption.disabled = hasCaption;
  ratingSubmit.disabled = hasCaption;
  ratingModal.classList.add("active");
}

function closeRatingModal() {
  ratingModal.classList.remove("active");
}

ratingCancel.onclick = closeRatingModal;

ratingSubmit.onclick = () => {
  if (!currentRatedItem) return;
  const caption = ratingCaption.value.trim();

  fetch(`/api/media/${currentRatedItem.id}/rating`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caption })
  }).then((res) => {
    if (res.ok) {
      currentRatedItem.rating_caption = caption;
      ratingNote.textContent = "Saved.";
      ratingCaption.disabled = true;
      ratingSubmit.disabled = true;
      closeRatingModal();
    } else {
      ratingNote.textContent = "Save failed.";
    }
  });
};

if (images.length) {
  bgImages.forEach((img) => {
    img.addEventListener("load", () => img.classList.add("is-loaded"));
    img.addEventListener("click", () => {
      const item = {
        id: Number(img.dataset.mediaId),
        url: img.src,
        model_name: img.dataset.modelName || "Unknown",
        rating: img.dataset.rating ? Number(img.dataset.rating) : null,
        rating_caption: img.dataset.caption || ""
      };
      openRatingModal(item);
    });
  });
  refreshBackgroundImages();
  bgImages[0].addEventListener("animationiteration", () => {
    if (!paused) refreshBackgroundImages();
  });
}
