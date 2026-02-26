// =====================
// HOME: model-viewer hotspots + calibración
// =====================

// Si cambiaste de GLB y querés calibración separada, versioná esto:
// const STORAGE_KEY = "car3d_hotspots_v2";
const STORAGE_KEY = "car3d_hotspots_v1";

function loadHotspotsFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function saveHotspotsToStorage(map) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
}

function applyStoredHotspots() {
  const map = loadHotspotsFromStorage();
  Object.entries(map).forEach(([slot, data]) => {
    const el = document.querySelector(`.mv-hotspot[slot="${slot}"]`);
    if (!el) return;
    if (data.position) el.setAttribute("data-position", data.position);
    if (data.normal) el.setAttribute("data-normal", data.normal);
  });
}

// 1) Click hotspot → rojo + navegar (HOME)
document.addEventListener("click", (e) => {
  const hs = e.target.closest(".mv-hotspot");
  if (!hs) return;

  const target = hs.getAttribute("data-target");
  if (!target) return;

  document.querySelectorAll(".mv-hotspot").forEach(b => b.classList.remove("is-active"));
  hs.classList.add("is-active");

  setTimeout(() => {
    window.location.href = target;
  }, 150);
});

// 2) Calibración: ALT/SHIFT/CTRL + click en el modelo = capturar hit (HOME)
(function () {
  const mv = document.getElementById("carModel");
  if (!mv) return; // si no está el viewer del home, no hacemos nada

  const out = document.getElementById("calibOut");
  let lastHit = null;

  // aplicar coordenadas guardadas
  applyStoredHotspots();

  // helper: soporta hit sync o Promise
  async function resolveHit(hitMaybePromise) {
    if (!hitMaybePromise) return null;
    if (typeof hitMaybePromise.then === "function") {
      return await hitMaybePromise;
    }
    return hitMaybePromise;
  }

  mv.addEventListener("click", async (e) => {
    const wantsCapture = e.altKey || e.shiftKey || e.ctrlKey;
    if (!wantsCapture) return;

    const rect = mv.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let hit = null;
    try {
      hit = await resolveHit(mv.positionAndNormalFromPoint(x, y));
    } catch (err) {
      console.log("Error positionAndNormalFromPoint:", err);
    }

    if (!hit || !hit.position || !hit.normal) {
      console.log("No hit (no se detectó superficie). Probá otro ángulo o más cerca del modelo.");
      if (out) out.value = "❌ No hit: probá otra zona del modelo o acercate con zoom.";
      return;
    }

    const position = hit.position.toString();
    const normal = hit.normal.toString();

    lastHit = { position, normal };

    const text = `✅ CAPTURADO\n\ndata-position="${position}"\ndata-normal="${normal}"`;
    console.log("HOTSPOT COORDS:\n", text);

    if (out) out.value = text;

    try {
      await navigator.clipboard.writeText(`data-position="${position}"\ndata-normal="${normal}"`);
    } catch (err) {
      console.log("No se pudo copiar al portapapeles:", err);
    }
  });

  // 3) Botones "Asignar → ..." (HOME)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-assign]");
    if (!btn) return;

    if (!lastHit) {
      alert("Primero capturá coordenadas: ALT/SHIFT/CTRL + click sobre la parte del modelo.");
      return;
    }

    const slot = btn.getAttribute("data-assign");
    const el = document.querySelector(`.mv-hotspot[slot="${slot}"]`);
    if (!el) {
      alert(`No encontré el hotspot con slot="${slot}".`);
      return;
    }

    el.setAttribute("data-position", lastHit.position);
    el.setAttribute("data-normal", lastHit.normal);

    const map = loadHotspotsFromStorage();
    map[slot] = { position: lastHit.position, normal: lastHit.normal };
    saveHotspotsToStorage(map);

    document.querySelectorAll(".mv-hotspot").forEach(b => b.classList.remove("is-active"));
    el.classList.add("is-active");
  });

  // 4) Reset calibración (HOME)
  document.addEventListener("click", (e) => {
    const reset = e.target.closest("[data-calib-reset]");
    if (!reset) return;

    localStorage.removeItem(STORAGE_KEY);
    document.querySelectorAll(".mv-hotspot").forEach(el => {
      el.setAttribute("data-position", "0m 0m 0m");
      el.setAttribute("data-normal", "0m 1m 0m");
      el.classList.remove("is-active");
    });

    if (out) out.value = "";
    lastHit = null;
  });
})();


// =====================
// AUTOS PAGE: viewer + search filter + enter loads first result
// =====================
(function () {
  const search = document.getElementById("carSearch");
  const grid = document.getElementById("autosGrid");
  const empty = document.getElementById("autosEmpty");

  // Si no estamos en /autos, salimos
  if (!search || !grid) return;

  console.log("[Autos] módulo cargado ✅", { search, grid, empty });
  const viewer = document.getElementById("autosViewer");
  const title = document.getElementById("autosTitle");

  function normalize(s) {
    return (s || "").toLowerCase().trim();
  }

  function getFilterText(btn) {
    // Preferimos data-filter; si no existe, armamos uno por seguridad
    const df = btn.getAttribute("data-filter");
    if (df) return normalize(df);

    const name = btn.getAttribute("data-car-name") || "";
    const slug = btn.getAttribute("data-car-slug") || "";
    return normalize(`${name} ${slug}`);
  }

  function applyFilter() {
    const q = normalize(search.value);
    let visibleCount = 0;

    grid.querySelectorAll(".autos__item").forEach((btn) => {
      const hay = getFilterText(btn);
      const ok = !q || hay.includes(q);

      btn.style.display = ok ? "" : "none";
      if (ok) visibleCount++;
    });

    if (empty) empty.style.display = visibleCount === 0 ? "" : "none";

    console.log("[Autos] filtro:", { q, visibleCount });
  }

  function getFirstVisibleItem() {
    return Array.from(grid.querySelectorAll(".autos__item"))
      .find((el) => el.style.display !== "none");
  }

  function loadIntoViewer(item) {
    const src = item.getAttribute("data-car-src");
    const name = item.getAttribute("data-car-name");

    if (viewer && src) viewer.setAttribute("src", src);
    if (title && name) title.textContent = name;
  }

  // Click en card -> cambia el GLB del viewer
  document.addEventListener("click", (e) => {
    const item = e.target.closest(".autos__item");
    if (!item) return;
    loadIntoViewer(item);
  });

  // Filtro en vivo
  search.addEventListener("input", applyFilter);

  // Enter: filtra y carga el primer resultado visible
  search.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();

    applyFilter();
    const first = getFirstVisibleItem();
    if (first) loadIntoViewer(first);
  });

  // init
  applyFilter();
})();