const modelsDataEl = document.getElementById("models-data");
const modelsData = modelsDataEl ? JSON.parse(modelsDataEl.textContent) : {};
const searchInput = document.getElementById("model-search");
const filterButtons = document.querySelectorAll(".pill[data-filter]");
const visibleCount = document.getElementById("models-visible-count");
let currentFilter = "all";

function deleteModel(slug) {
  if (!confirm(`Delete model "${slug}" and all its media? This cannot be undone.`)) {
    return;
  }

  fetch(`/models/${slug}`, {
    method: "DELETE",
  }).then((res) => {
    if (res.ok) {
      location.reload();
    } else {
      alert("Failed to delete model.");
    }
  });
}

document.querySelectorAll(".model-image img").forEach((img) => {
  if (img.complete) {
    img.classList.add("is-loaded");
  } else {
    img.addEventListener("load", () => img.classList.add("is-loaded"));
  }
});

document.querySelectorAll(".model-image video").forEach((video) => {
  if (video.readyState >= 2) {
    video.classList.add("is-loaded");
  } else {
    video.addEventListener("loadeddata", () => video.classList.add("is-loaded"));
  }
});

document.querySelectorAll(".model-card").forEach((card) => {
  const link = card.querySelector(".model-actions a");
  if (!link) return;
  card.addEventListener("click", (event) => {
    const target = event.target;
    if (target.closest("a") || target.closest("button")) return;
    window.location.href = link.href;
  });
});

function normalizeText(value) {
  return value.toLowerCase().replace(/_/g, " ").replace(/\s+/g, " ").trim();
}

function applyFilters() {
  const query = normalizeText(searchInput ? searchInput.value : "");
  let shown = 0;

  document.querySelectorAll(".model-card").forEach((card) => {
    const name = normalizeText(card.dataset.name || "");
    const imageCount = Number(card.dataset.imageCount || 0);
    const videoCount = Number(card.dataset.videoCount || 0);

    const matchesQuery = !query || name.includes(query);
    const matchesFilter = (
      currentFilter === "all" ||
      (currentFilter === "photos" && imageCount > 0) ||
      (currentFilter === "videos" && videoCount > 0)
    );

    const isVisible = matchesQuery && matchesFilter;
    card.style.display = isVisible ? "" : "none";
    if (isVisible) shown += 1;
  });

  if (visibleCount) {
    visibleCount.textContent = String(shown);
  }
}

if (searchInput) {
  searchInput.addEventListener("input", () => {
    applyFilters();
  });
}

filterButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    currentFilter = btn.dataset.filter || "all";
    filterButtons.forEach((button) => {
      const isActive = button === btn;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    applyFilters();
  });
});

applyFilters();

window.deleteModel = deleteModel;
