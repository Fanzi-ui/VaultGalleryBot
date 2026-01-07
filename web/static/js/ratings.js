const ratingsDataEl = document.getElementById("ratings-data");
const ratingsData = ratingsDataEl ? JSON.parse(ratingsDataEl.textContent) : {};
const adminToken = ratingsData.adminToken || "";
const countEl = document.getElementById("ratings-count");

function updateCount(delta) {
  if (!countEl) return;
  const current = Number(countEl.textContent || "0");
  const next = Math.max(current + delta, 0);
  countEl.textContent = String(next);
}

document.querySelectorAll(".rating-card").forEach((card) => {
  const saveBtn = card.querySelector(".save-rating");
  const skipBtn = card.querySelector(".skip-rating");
  const textarea = card.querySelector("textarea");
  const status = card.querySelector(".rating-status");
  const mediaId = card.dataset.id;

  if (skipBtn) {
    skipBtn.addEventListener("click", () => {
      card.remove();
      updateCount(-1);
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const caption = textarea ? textarea.value.trim() : "";
      saveBtn.disabled = true;
      if (status) status.textContent = "Saving...";

      fetch(`/api/media/${mediaId}/rating`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(adminToken ? { "X-Admin-Token": adminToken } : {}),
        },
        body: JSON.stringify({ caption }),
      }).then((res) => {
        if (res.ok) {
          if (status) status.textContent = "Saved.";
          card.remove();
          updateCount(-1);
        } else {
          if (status) status.textContent = "Save failed.";
          saveBtn.disabled = false;
        }
      }).catch(() => {
        if (status) status.textContent = "Save failed.";
        saveBtn.disabled = false;
      });
    });
  }
});
