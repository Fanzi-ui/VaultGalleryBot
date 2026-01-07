const galleryDataEl = document.getElementById("gallery-data");
const galleryData = galleryDataEl ? JSON.parse(galleryDataEl.textContent) : {};
const media = galleryData.media || [];
const adminToken = galleryData.adminToken || "";
const hasNextPage = Boolean(galleryData.hasNextPage);
const hasPrevPage = Boolean(galleryData.hasPrevPage);
const nextPageUrl = galleryData.nextPageUrl || "";
const prevPageUrl = galleryData.prevPageUrl || "";
const deleteTokenQuery = adminToken ? `?token=${encodeURIComponent(adminToken)}` : "";
const ratingFilters = document.querySelectorAll("[data-rating-filter]");
const typeFilters = document.querySelectorAll("[data-type-filter]");
const sortButtons = document.querySelectorAll("[data-sort]");
const visibleCount = document.getElementById("gallery-visible-count");
const galleryGrid = document.querySelector(".gallery-grid");
const itemNodes = Array.from(document.querySelectorAll(".gallery-item"));
const itemNodesByIndex = new Map(
  itemNodes.map((node) => [Number(node.dataset.index), node])
);

let currentVisibleIndex = 0;
let visibleIndices = [];
let ratingFilter = "all";
let typeFilter = "all";
let sortMode = "recent";

const lightbox = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightboxImage");
const lightboxVideo = document.getElementById("lightboxVideo");

itemNodes.forEach((item) => {
  item.addEventListener("click", () => {
    openLightboxFromMediaIndex(Number(item.dataset.index));
  });
});

document.querySelectorAll(".gallery-item img").forEach((img) => {
  if (img.complete) {
    img.classList.add("is-loaded");
  } else {
    img.addEventListener("load", () => img.classList.add("is-loaded"));
  }
});

document.querySelectorAll(".gallery-item video").forEach((video) => {
  if (video.readyState >= 2) {
    video.classList.add("is-loaded");
  } else {
    video.addEventListener("loadeddata", () => video.classList.add("is-loaded"));
  }
});

function appendParam(url, key, value) {
  if (!url) return url;
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
}

function openLightbox() {
  const mediaIndex = visibleIndices[currentVisibleIndex];
  const item = media[mediaIndex];
  if (!item) return;

  if (item.media_type === "video") {
    lightboxImage.style.display = "none";
    lightboxVideo.style.display = "block";
    lightboxVideo.src = item.url;
    lightboxVideo.currentTime = 0;
  } else {
    lightboxVideo.pause();
    lightboxVideo.removeAttribute("src");
    lightboxVideo.load();
    lightboxVideo.style.display = "none";
    lightboxImage.style.display = "block";
    lightboxImage.src = item.url;
  }
  lightbox.classList.add("active");
}

function closeLightbox() {
  lightboxVideo.pause();
  lightbox.classList.remove("active");
}

function nextImage() {
  if (!visibleIndices.length) return;
  if (currentVisibleIndex === visibleIndices.length - 1) {
    if (hasNextPage && nextPageUrl) {
      window.location.href = appendParam(nextPageUrl, "open", 0);
    }
    return;
  }
  currentVisibleIndex += 1;
  openLightbox();
}

function prevImage() {
  if (!visibleIndices.length) return;
  if (currentVisibleIndex === 0) {
    if (hasPrevPage && prevPageUrl) {
      const lastIndex = Math.max(media.length - 1, 0);
      window.location.href = appendParam(prevPageUrl, "open", lastIndex);
    }
    return;
  }
  currentVisibleIndex -= 1;
  openLightbox();
}

function deleteCurrent() {
  const mediaIndex = visibleIndices[currentVisibleIndex];
  const item = media[mediaIndex];
  if (!item) return;
  if (!confirm("Delete this media?")) return;

  fetch(`/api/media/${item.id}${deleteTokenQuery}`, {
    method: "DELETE",
    headers: adminToken ? { "X-Admin-Token": adminToken } : {}
  }).then((res) => {
    if (res.ok) location.reload();
    else alert("Delete failed");
  });
}

document.addEventListener("keydown", (e) => {
  if (!lightbox.classList.contains("active")) return;

  if (e.key === "ArrowRight") nextImage();
  if (e.key === "ArrowLeft") prevImage();
  if (e.key === "Escape") closeLightbox();
});

const params = new URLSearchParams(window.location.search);
applyFilters();

if (params.has("open") && media.length) {
  const index = Number(params.get("open"));
  if (!Number.isNaN(index) && index >= 0 && index < media.length) {
    const visibleIndex = visibleIndices.indexOf(index);
    if (visibleIndex >= 0) {
      currentVisibleIndex = visibleIndex;
      openLightbox();
    }
  }
}

window.closeLightbox = closeLightbox;
window.deleteCurrent = deleteCurrent;

function normalizeRating(value) {
  if (value === null || value === undefined || value === "") return null;
  const num = Number(value);
  return Number.isNaN(num) ? null : num;
}

function applyFilters() {
  visibleIndices = [];

  itemNodes.forEach((node) => {
    const mediaIndex = Number(node.dataset.index);
    const item = media[mediaIndex];
    if (!item) return;

    const itemRating = normalizeRating(item.rating);
    const isRated = itemRating !== null;
    const matchesRating = (
      ratingFilter === "all" ||
      (ratingFilter === "rated" && isRated) ||
      (ratingFilter === "unrated" && !isRated)
    );

    const matchesType = (
      typeFilter === "all" ||
      item.media_type === typeFilter
    );

    const isVisible = matchesRating && matchesType;
    node.style.display = isVisible ? "" : "none";
    if (isVisible) {
      visibleIndices.push(mediaIndex);
    }
  });

  if (sortMode === "rating") {
    visibleIndices.sort((a, b) => {
      const aRating = normalizeRating(media[a]?.rating) ?? -1;
      const bRating = normalizeRating(media[b]?.rating) ?? -1;
      if (aRating === bRating) return a - b;
      return bRating - aRating;
    });
  } else {
    visibleIndices.sort((a, b) => a - b);
  }

  if (galleryGrid) {
    const fragment = document.createDocumentFragment();
    const visibleSet = new Set(visibleIndices);

    visibleIndices.forEach((index) => {
      const node = itemNodesByIndex.get(index);
      if (node) fragment.appendChild(node);
    });

    itemNodes.forEach((node) => {
      const index = Number(node.dataset.index);
      if (!visibleSet.has(index)) fragment.appendChild(node);
    });

    galleryGrid.appendChild(fragment);
  }

  if (visibleCount) {
    visibleCount.textContent = String(visibleIndices.length);
  }

  if (!visibleIndices.length && lightbox.classList.contains("active")) {
    closeLightbox();
  }
}

function setActiveButton(buttons, activeButton) {
  buttons.forEach((button) => {
    const isActive = button === activeButton;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

function openLightboxFromMediaIndex(mediaIndex) {
  const visibleIndex = visibleIndices.indexOf(mediaIndex);
  if (visibleIndex < 0) return;
  currentVisibleIndex = visibleIndex;
  openLightbox();
}

ratingFilters.forEach((button) => {
  button.addEventListener("click", () => {
    ratingFilter = button.dataset.ratingFilter || "all";
    setActiveButton(ratingFilters, button);
    closeLightbox();
    applyFilters();
  });
});

typeFilters.forEach((button) => {
  button.addEventListener("click", () => {
    typeFilter = button.dataset.typeFilter || "all";
    setActiveButton(typeFilters, button);
    closeLightbox();
    applyFilters();
  });
});

sortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    sortMode = button.dataset.sort || "recent";
    setActiveButton(sortButtons, button);
    applyFilters();
  });
});
