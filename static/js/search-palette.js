/**

 * Command palette — CTRL+K / CMD+K global search

 */

const SearchPalette = (() => {

    let activeIdx = -1;

    let filtered = [];



    function tw() {

        return typeof TW !== "undefined" ? TW : null;

    }



    function paletteClasses() {

        const t = tw();

        return {

            result: t?.paletteResult || "palette-result flex items-center gap-3 rounded-lg px-3 py-3 text-text no-underline transition hover:bg-primary-soft",

            resultActive: t?.paletteResultActive || "palette-result active flex items-center gap-3 rounded-lg bg-primary-soft px-3 py-3 text-text no-underline transition",

            icon: t?.paletteResultIcon || "palette-result-icon flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-bg text-primary",

            cat: t?.paletteCatBadge || "inline-flex shrink-0 items-center gap-1 rounded-full border border-border bg-bg px-2 py-0.5 text-[0.72rem] font-semibold text-text-muted",

        };

    }



    function escapeHtml(text) {

        return String(text).replace(/[&<>"']/g, c => ({

            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"

        }[c]));

    }



    function getTools() {

        return window.__TOOL_INDEX__ || [];

    }



    function isOpen(overlay) {

        return overlay && !overlay.classList.contains("hidden");

    }



    function open() {

        const overlay = document.getElementById("search-palette");

        const input = document.getElementById("palette-input");

        if (!overlay || !input) return;

        overlay.classList.remove("hidden");

        overlay.classList.add("open");

        overlay.setAttribute("aria-hidden", "false");

        input.value = "";

        input.focus();

        activeIdx = -1;

        render("");

        document.body.style.overflow = "hidden";

    }



    function close() {

        const overlay = document.getElementById("search-palette");

        if (!overlay) return;

        overlay.classList.add("hidden");

        overlay.classList.remove("open");

        overlay.setAttribute("aria-hidden", "true");

        document.body.style.overflow = "";

        activeIdx = -1;

    }



    function render(query) {

        const list = document.getElementById("palette-results");

        if (!list) return;

        const q = query.trim().toLowerCase();

        const tools = getTools().filter(t => !t.disabled);

        const favorites = typeof Favorites !== "undefined" ? Favorites.getAll() : [];

        const favSet = new Set(favorites.map(f => f.href));

        const cls = paletteClasses();



        filtered = !q

            ? tools.slice(0, 12)

            : tools.filter(t =>

                t.name.toLowerCase().includes(q) ||

                t.catName.toLowerCase().includes(q) ||

                (t.desc || "").toLowerCase().includes(q) ||

                t.href.toLowerCase().includes(q)

            ).slice(0, 12);



        if (filtered.length === 0) {

            list.innerHTML = `<div class="palette-empty px-6 py-8 text-center text-sm text-text-muted">No tools found for "${escapeHtml(query)}"</div>`;

            return;

        }



        list.innerHTML = filtered.map((t, i) => `

            <a href="${t.href}" class="${i === activeIdx ? cls.resultActive : cls.result}" role="option" data-idx="${i}">

                <span class="${cls.icon}"><i class="bi ${t.icon}"></i></span>

                <span class="palette-result-body min-w-0 flex-1">

                    <span class="palette-result-name block text-sm font-semibold">${escapeHtml(t.name)}${favSet.has(t.href) ? ' <i class="bi bi-star-fill text-[0.7rem] text-warning"></i>' : ""}</span>

                    <span class="palette-result-desc block truncate text-xs text-text-muted">${escapeHtml(t.desc || "")}</span>

                </span>

                <span class="${cls.cat}">${escapeHtml(t.catName)}</span>

            </a>

        `).join("");

    }



    function setActive(idx) {

        const list = document.getElementById("palette-results");

        if (!list) return;

        const cls = paletteClasses();

        const items = list.querySelectorAll(".palette-result");

        items.forEach((el, i) => {

            el.className = i === idx ? cls.resultActive : cls.result;

        });

        if (idx >= 0 && idx < items.length) {

            items[idx].scrollIntoView({ block: "nearest" });

        }

        activeIdx = idx;

    }



    function init() {

        const overlay = document.getElementById("search-palette");

        const input = document.getElementById("palette-input");

        if (!overlay || !input) return;



        document.addEventListener("keydown", e => {

            if ((e.ctrlKey || e.metaKey) && e.key === "k") {

                e.preventDefault();

                if (isOpen(overlay)) close();

                else open();

            }

            if (e.key === "Escape" && isOpen(overlay)) {

                close();

            }

        });



        overlay.querySelector("[data-palette-close]")?.addEventListener("click", close);



        input.addEventListener("input", () => {

            activeIdx = -1;

            render(input.value);

        });



        input.addEventListener("keydown", e => {

            const items = document.querySelectorAll("#palette-results .palette-result");

            if (e.key === "ArrowDown") {

                e.preventDefault();

                setActive(Math.min(activeIdx + 1, items.length - 1));

            } else if (e.key === "ArrowUp") {

                e.preventDefault();

                setActive(Math.max(activeIdx - 1, 0));

            } else if (e.key === "Enter" && activeIdx >= 0 && items[activeIdx]) {

                e.preventDefault();

                window.location.href = items[activeIdx].getAttribute("href");

            }

        });



        document.querySelectorAll("[data-open-palette]").forEach(el => {

            el.addEventListener("click", e => {

                e.preventDefault();

                open();

            });

        });

    }



    return { open, close, init };

})();

