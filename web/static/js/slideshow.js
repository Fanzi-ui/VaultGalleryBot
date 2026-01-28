const slideshowDataEl = document.getElementById("slideshow-data");
const slideshowData = slideshowDataEl ? JSON.parse(slideshowDataEl.textContent) : {};
const mediaItems = slideshowData.media || [];

const slideshowEl = document.querySelector(".slideshow");
const stageEl = document.getElementById("slideshow-stage");
const hudMeta = document.getElementById("hud-meta");
const hudCounter = document.getElementById("hud-counter");
const hudToggle = document.getElementById("hud-toggle");
const hudBack = document.getElementById("hud-back");

const modeButtons = document.querySelectorAll("[data-mode]");
const modelFilter = document.getElementById("model-filter");
const typeFilter = document.getElementById("type-filter");
const ratingFilter = document.getElementById("rating-filter");
const speedRange = document.getElementById("speed-range");
const speedValue = document.getElementById("speed-value");
const pauseToggle = document.getElementById("pause-toggle");
const prevToggle = document.getElementById("prev-toggle");
const nextToggle = document.getElementById("next-toggle");
const muteToggle = document.getElementById("mute-toggle");
const fullscreenToggle = document.getElementById("fullscreen-toggle");

const layers = [
  document.getElementById("slide-a"),
  document.getElementById("slide-b"),
];

let activeLayerIndex = 0;
let queue = [];
let currentIndex = -1;
let mode = "drift";
let isPaused = false;
let isMuted = true;
let timerId = null;
let idleTimerId = null;
const history = [];
const queryParams = new URLSearchParams(window.location.search);

function normalizeText(value) {
  return value.toLowerCase().replace(/_/g, " ").trim();
}

function shuffle(list) {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function filteredMedia() {
  const modelValue = normalizeText(modelFilter?.value || "");
  const typeValue = (typeFilter?.value || "").toLowerCase();
  const ratingValue = ratingFilter?.value || "";

  return mediaItems.filter((item) => {
    const matchesModel = !modelValue || normalizeText(item.model_name || "").includes(modelValue);
    const matchesType = !typeValue || item.media_type === typeValue;
    const isRated = item.rating !== null && item.rating !== undefined;
    const matchesRating = (
      ratingValue === "" ||
      (ratingValue === "rated" && isRated) ||
      (ratingValue === "unrated" && !isRated)
    );

    return matchesModel && matchesType && matchesRating;
  });
}

function applyQueryDefaults() {
  const modelParam = queryParams.get("model");
  const typeParam = queryParams.get("type");
  const ratingParam = queryParams.get("rating");
  const modeParam = queryParams.get("mode");
  const speedParam = queryParams.get("speed");

  if (modelFilter && modelParam) {
    modelFilter.value = modelParam;
  }
  if (typeFilter && typeParam) {
    typeFilter.value = typeParam;
  }
  if (ratingFilter && ratingParam) {
    ratingFilter.value = ratingParam;
  }
  if (speedRange && speedParam) {
    const speed = Number(speedParam);
    if (!Number.isNaN(speed)) {
      speedRange.value = String(Math.max(4, Math.min(16, speed)));
      if (speedValue) speedValue.textContent = `${speedRange.value}s`;
    }
  }
  if (modeParam) {
    const target = Array.from(modeButtons).find((button) => button.dataset.mode === modeParam);
    if (target) {
      mode = modeParam;
      setActiveButton(modeButtons, target);
    }
  }
}

function buildQueue() {
  const list = filteredMedia();
  if (!list.length) {
    queue = [];
    setHudCounter(null);
    return;
  }

  const indices = list.map((item) => mediaItems.indexOf(item)).filter((index) => index >= 0);
  queue = mode === "shuffle" ? shuffle(indices) : indices;
}

function setActiveButton(buttons, activeButton) {
  buttons.forEach((button) => {
    const isActive = button === activeButton;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

function setHudText(item) {
  if (!hudMeta) return;
  if (!item) {
    hudMeta.textContent = "No media available";
    return;
  }
  const ratingLabel = item.rating ? `Rating ${item.rating}` : "Unrated";
  const typeLabel = item.media_type === "video" ? "Video" : "Image";
  hudMeta.textContent = `${item.model_name || "Unknown"} • ${typeLabel} • ${ratingLabel}`;
}

function setHudCounter(item) {
  if (!hudCounter) return;
  const list = filteredMedia();
  const total = list.length;
  if (!item || total === 0) {
    hudCounter.textContent = "0 / 0";
    return;
  }
  const index = list.findIndex((entry) => entry.id === item.id);
  const position = index >= 0 ? index + 1 : 0;
  hudCounter.textContent = `${position} / ${total}`;
}

function setLayerContent(layer, item) {
  const imageEl = layer.querySelector(".slide-image");
  const videoEl = layer.querySelector(".slide-video");

  if (!item) {
    imageEl.removeAttribute("src");
    videoEl.removeAttribute("src");
    videoEl.load();
    setHudText(null);
    return;
  }

  if (item.media_type === "video") {
    layer.classList.add("is-video");
    videoEl.src = item.url;
    videoEl.muted = isMuted;
    videoEl.currentTime = 0;
    const playPromise = videoEl.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {});
    }
  } else {
    layer.classList.remove("is-video");
    imageEl.src = item.url;
    videoEl.pause();
    videoEl.removeAttribute("src");
    videoEl.load();
  }

  setHudText(item);
  setHudCounter(item);
}

function swapLayers() {
  layers[activeLayerIndex].classList.remove("is-active");
  activeLayerIndex = (activeLayerIndex + 1) % layers.length;
  layers[activeLayerIndex].classList.add("is-active");
}

function showSlide(item) {
  const inactiveLayer = layers[(activeLayerIndex + 1) % layers.length];
  setLayerContent(inactiveLayer, item);
  requestAnimationFrame(() => {
    swapLayers();
  });
}

function nextSlide() {
  if (!queue.length) {
    buildQueue();
  }
  if (!queue.length) {
    showSlide(null);
    return;
  }
  const nextIndex = queue.shift();
  if (currentIndex >= 0) {
    history.push(currentIndex);
  }
  currentIndex = nextIndex;
  const item = mediaItems[nextIndex];
  showSlide(item);
}

function prevSlide() {
  if (!history.length) return;
  const prevIndex = history.pop();
  currentIndex = prevIndex;
  const item = mediaItems[prevIndex];
  showSlide(item);
}

function scheduleNext() {
  if (timerId) clearTimeout(timerId);
  const speedSeconds = Number(speedRange?.value || 8);
  if (speedValue) speedValue.textContent = `${speedSeconds}s`;
  timerId = setTimeout(() => {
    if (!isPaused) {
      nextSlide();
      scheduleNext();
    }
  }, speedSeconds * 1000);
}

function startSlideshow() {
  buildQueue();
  nextSlide();
  scheduleNext();
}

function handleIdle() {
  if (!slideshowEl) return;
  slideshowEl.classList.add("is-idle");
}

function resetIdle() {
  if (!slideshowEl) return;
  slideshowEl.classList.remove("is-idle");
  if (idleTimerId) clearTimeout(idleTimerId);
  idleTimerId = setTimeout(handleIdle, 3200);
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    mode = button.dataset.mode || "drift";
    setActiveButton(modeButtons, button);
    if (stageEl) stageEl.dataset.mode = mode;
    buildQueue();
  });
});

[modelFilter, typeFilter, ratingFilter].forEach((control) => {
  if (!control) return;
  control.addEventListener("change", () => {
    buildQueue();
  });
});

if (speedRange) {
  speedRange.addEventListener("input", () => {
    if (speedValue) speedValue.textContent = `${speedRange.value}s`;
    scheduleNext();
  });
}

if (pauseToggle) {
  pauseToggle.addEventListener("click", () => {
    isPaused = !isPaused;
    pauseToggle.textContent = isPaused ? "Resume" : "Pause";
    if (!isPaused) {
      scheduleNext();
    }
  });
}

if (nextToggle) {
  nextToggle.addEventListener("click", () => {
    nextSlide();
    scheduleNext();
  });
}

if (prevToggle) {
  prevToggle.addEventListener("click", () => {
    prevSlide();
    scheduleNext();
  });
}

if (muteToggle) {
  muteToggle.addEventListener("click", () => {
    isMuted = !isMuted;
    muteToggle.textContent = isMuted ? "Sound" : "Mute";
    const activeVideo = layers[activeLayerIndex].querySelector(".slide-video");
    if (activeVideo) {
      activeVideo.muted = isMuted;
    }
  });
}

if (fullscreenToggle) {
  fullscreenToggle.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      stageEl.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });
}

if (hudToggle) {
  hudToggle.addEventListener("click", () => {
    slideshowEl.classList.toggle("is-idle");
  });
}

if (hudBack) {
  hudBack.addEventListener("click", () => {
    window.location.href = "/";
  });
}

document.addEventListener("keydown", (event) => {
  if (event.target && ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) {
    return;
  }
  if (event.key === " ") {
    event.preventDefault();
    pauseToggle?.click();
  }
  if (event.key === "ArrowRight") nextToggle?.click();
  if (event.key === "ArrowLeft") prevToggle?.click();
  if (event.key.toLowerCase() === "m") muteToggle?.click();
  if (event.key.toLowerCase() === "f") fullscreenToggle?.click();
  if (event.key.toLowerCase() === "h") hudToggle?.click();
});

["mousemove", "keydown", "touchstart"].forEach((eventName) => {
  document.addEventListener(eventName, resetIdle, { passive: true });
});

resetIdle();
applyQueryDefaults();
if (stageEl) stageEl.dataset.mode = mode;
if (muteToggle) muteToggle.textContent = isMuted ? "Sound" : "Mute";
startSlideshow();
