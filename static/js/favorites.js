/**
 * Favorites system — localStorage pin/unpin tools
 */
const Favorites = (() => {
    const KEY = "everytools:favorites";

    function getAll() {
        try {
            return JSON.parse(localStorage.getItem(KEY) || "[]");
        } catch {
            return [];
        }
    }

    function save(list) {
        localStorage.setItem(KEY, JSON.stringify(list));
        window.dispatchEvent(new CustomEvent("everytools:favorites-changed"));
    }

    function toolKey(catId, toolId) {
        return `${catId}/${toolId}`;
    }

    function isFavorite(catId, toolId) {
        return getAll().some(f => f.catId === catId && f.toolId === toolId);
    }

    function toggle(catId, toolId, meta = {}) {
        const list = getAll();
        const idx = list.findIndex(f => f.catId === catId && f.toolId === toolId);
        if (idx >= 0) {
            list.splice(idx, 1);
        } else {
            list.unshift({
                catId,
                toolId,
                name: meta.name || toolId,
                desc: meta.desc || "",
                icon: meta.icon || "bi-tools",
                catName: meta.catName || catId,
                href: meta.href || `/${catId}/${toolId}`,
                pinnedAt: Date.now(),
            });
        }
        save(list.slice(0, 50));
        return idx < 0;
    }

    function remove(catId, toolId) {
        save(getAll().filter(f => !(f.catId === catId && f.toolId === toolId)));
    }

    function renderPinButtons() {
        document.querySelectorAll("[data-favorite]").forEach(btn => {
            const catId = btn.dataset.catId;
            const toolId = btn.dataset.toolId;
            const pinned = isFavorite(catId, toolId);
            if (typeof TW !== "undefined") {
                btn.className = pinned ? TW.pinBtnPinned : TW.pinBtn;
            } else {
                btn.classList.toggle("pinned", pinned);
            }
            btn.setAttribute("aria-pressed", pinned ? "true" : "false");
            btn.title = pinned ? "Remove from favorites" : "Add to favorites";
            const icon = btn.querySelector("i");
            if (icon) {
                icon.className = pinned ? "bi bi-star-fill" : "bi bi-star";
            }
        });
    }

    function init() {
        document.addEventListener("click", e => {
            const btn = e.target.closest("[data-favorite]");
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            toggle(btn.dataset.catId, btn.dataset.toolId, {
                name: btn.dataset.toolName,
                desc: btn.dataset.toolDesc,
                icon: btn.dataset.toolIcon,
                catName: btn.dataset.catName,
                href: btn.dataset.href,
            });
            renderPinButtons();
            if (typeof SidebarUI !== "undefined") SidebarUI.refreshFavorites();
            if (typeof DashboardUI !== "undefined") DashboardUI.refreshSuggested();
        });
        renderPinButtons();
        window.addEventListener("everytools:favorites-changed", renderPinButtons);
    }

    return { getAll, isFavorite, toggle, remove, init, renderPinButtons, toolKey };
})();
