const galleryDataEl = document.getElementById("gallery-data");
const galleryData = galleryDataEl ? JSON.parse(galleryDataEl.textContent) : {};
const media = galleryData.media || [];
let hasNextPage = Boolean(galleryData.hasNextPage);
let hasPrevPage = Boolean(galleryData.hasPrevPage);
let nextPageUrl = galleryData.nextPageUrl || "";
let prevPageUrl = galleryData.prevPageUrl || "";
const ratingFilters = document.querySelectorAll("[data-rating-filter]");
const typeFilters = document.querySelectorAll("[data-type-filter]");
const sortButtons = document.querySelectorAll("[data-sort]");
const resetFiltersButton = document.querySelector("[data-action='reset-filters']");
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
let loadingNextPage = false;
let observer = null;

const lightbox = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightboxImage");
const lightboxVideo = document.getElementById("lightboxVideo");
const lightboxCloseButtons = Array.from(
  document.querySelectorAll("#lightbox-close")
);
const lightboxDeleteButton = document.getElementById("lightbox-delete");
const lightboxModel = document.getElementById("lightbox-model");
const lightboxDetails = document.getElementById("lightbox-details");

itemNodes.forEach((item) => {
  item.addEventListener("click", () => {
    openLightboxFromMediaIndex(Number(item.dataset.index));
  });
});

function wireMediaLoadStates(container = document) {
  container.querySelectorAll(".gallery-item img").forEach((img) => {
    if (img.complete) {
      img.classList.add("is-loaded");
    } else {
      img.addEventListener("load", () => img.classList.add("is-loaded"));
    }
  });

  container.querySelectorAll(".gallery-item video").forEach((video) => {
    if (video.readyState >= 2) {
      video.classList.add("is-loaded");
    } else {
      video.addEventListener("loadeddata", () => video.classList.add("is-loaded"));
    }
  });
}

wireMediaLoadStates();

function appendParam(url, key, value) {
  if (!url) return url;
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
}

function formatDate(isoString) {
  if (!isoString) return "Unknown";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

function updateLightboxMeta(item) {
  if (lightboxModel) {
    lightboxModel.textContent = item.model_name || "";
  }
  if (lightboxDetails) {
    const ratingText = item.rating ? `Rating ${item.rating}` : "Unrated";
    const dateText = formatDate(item.created_at);
    const typeText = item.media_type ? item.media_type.toUpperCase() : "MEDIA";
    lightboxDetails.textContent = `${typeText} • ${ratingText} • ${dateText}`;
  }
}

function openLightbox() {
  if (!lightbox) return;
  const mediaIndex = visibleIndices[currentVisibleIndex];
  const item = media[mediaIndex];
  if (!item) return;

  updateLightboxMeta(item);

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
  if (!lightbox) return;
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

  fetch(`/api/media/${item.id}`, {
    method: "DELETE",
  }).then((res) => {
    if (res.ok) location.reload();
    else alert("Delete failed");
  });
}

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

    const matchesType = typeFilter === "all" || item.media_type === typeFilter;

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

  if (!visibleIndices.length && lightbox && lightbox.classList.contains("active")) {
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

function resetFilters() {
  ratingFilter = "all";
  typeFilter = "all";
  sortMode = "recent";

  const defaultRating = document.querySelector("[data-rating-filter='all']");
  const defaultType = document.querySelector("[data-type-filter='all']");
  const defaultSort = document.querySelector("[data-sort='recent']");

  if (ratingFilters.length && defaultRating) {
    setActiveButton(ratingFilters, defaultRating);
  }
  if (typeFilters.length && defaultType) {
    setActiveButton(typeFilters, defaultType);
  }
  if (sortButtons.length && defaultSort) {
    setActiveButton(sortButtons, defaultSort);
  }
  applyFilters();
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
    applyFilters();
  });
});

typeFilters.forEach((button) => {
  button.addEventListener("click", () => {
    typeFilter = button.dataset.typeFilter || "all";
    setActiveButton(typeFilters, button);
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

if (resetFiltersButton) {
  resetFiltersButton.addEventListener("click", resetFilters);
}

function createSentinel() {
  if (!galleryGrid) return null;
  let sentinel = document.querySelector(".gallery-sentinel");
  if (!sentinel) {
    sentinel = document.createElement("div");
    sentinel.className = "gallery-sentinel";
    galleryGrid.insertAdjacentElement("afterend", sentinel);
  }
  return sentinel;
}

async function loadNextPage() {
  if (!hasNextPage || !nextPageUrl || loadingNextPage) return;
  loadingNextPage = true;

  try {
    const response = await fetch(nextPageUrl, { credentials: "same-origin" });
    if (!response.ok) {
      loadingNextPage = false;
      return;
    }
    const html = await response.text();
    const doc = new DOMParser().parseFromString(html, "text/html");
    const dataEl = doc.getElementById("gallery-data");
    if (!dataEl) {
      loadingNextPage = false;
      return;
    }
    const nextData = JSON.parse(dataEl.textContent);
    const newMedia = nextData.media || [];

    hasNextPage = Boolean(nextData.hasNextPage);
    hasPrevPage = Boolean(nextData.hasPrevPage);
    nextPageUrl = nextData.nextPageUrl || "";
    prevPageUrl = nextData.prevPageUrl || "";

    const newNodes = Array.from(doc.querySelectorAll(".gallery-item"));
    const baseIndex = media.length;

    newNodes.forEach((node, idx) => {
      const newIndex = baseIndex + idx;
      const item = newMedia[idx];
      if (!item) return;

      node.dataset.index = String(newIndex);
      node.dataset.id = String(item.id);
      node.dataset.rating = item.rating ?? "";
      node.dataset.mediaType = item.media_type;

      node.addEventListener("click", () => {
        openLightboxFromMediaIndex(newIndex);
      });

      const imported = document.importNode(node, true);
      galleryGrid.appendChild(imported);
      itemNodes.push(imported);
      itemNodesByIndex.set(newIndex, imported);
    });

    media.push(...newMedia);
    wireMediaLoadStates(galleryGrid);
    applyFilters();

    if (!hasNextPage && observer) {
      observer.disconnect();
    }
  } catch (_err) {
    // Ignore fetch errors for now.
  } finally {
    loadingNextPage = false;
  }
}

function setupInfiniteScroll() {
  const sentinel = createSentinel();
  if (!sentinel) return;

  if ("IntersectionObserver" in window) {
    observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          loadNextPage();
        }
      });
    });
    observer.observe(sentinel);
  } else {
    window.addEventListener("scroll", () => {
      const threshold = document.documentElement.scrollHeight - window.innerHeight - 300;
      if (window.scrollY >= threshold) {
        loadNextPage();
      }
    });
  }
}

const params = new URLSearchParams(window.location.search);
applyFilters();
setupInfiniteScroll();

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

document.addEventListener("keydown", (e) => {
  if (!lightbox || !lightbox.classList.contains("active")) return;
  if (e.key === "ArrowRight") nextImage();
  if (e.key === "ArrowLeft") prevImage();
  if (e.key === "Escape") closeLightbox();
  if (e.key === "Delete") deleteCurrent();
});

lightboxCloseButtons.forEach((btn) => {
  btn.addEventListener("click", closeLightbox);
});

if (lightboxDeleteButton) {
  lightboxDeleteButton.addEventListener("click", deleteCurrent);
}

if (lightbox) {
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });

  let touchStartX = 0;
  let touchStartY = 0;
  let touchStartTime = 0;

  lightbox.addEventListener("touchstart", (event) => {
    if (event.touches.length !== 1) return;
    const touch = event.touches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    touchStartTime = Date.now();
  });

  lightbox.addEventListener("touchend", (event) => {
    if (event.changedTouches.length !== 1) return;
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - touchStartX;
    const deltaY = touch.clientY - touchStartY;
    const elapsed = Date.now() - touchStartTime;

    if (elapsed > 600) return;
    if (Math.abs(deltaX) < 50 || Math.abs(deltaY) > 60) return;

    if (deltaX < 0) {
      nextImage();
    } else {
      prevImage();
    }
  });
}
