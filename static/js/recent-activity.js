/**
 * Recent activity — track tool opens, executions, and processed files
 */
const RecentActivity = (() => {
    const TOOLS_KEY = "everytools:recent-tools";
    const FILES_KEY = "everytools:recent-files";
    const USAGE_KEY = "everytools:tool-usage";
    const MAX_TOOLS = 20;
    const MAX_FILES = 15;

    function load(key) {
        try {
            return JSON.parse(localStorage.getItem(key) || "[]");
        } catch {
            return [];
        }
    }

    function save(key, list) {
        localStorage.setItem(key, JSON.stringify(list));
        window.dispatchEvent(new CustomEvent("everytools:recent-changed"));
    }

    function trackToolOpen(meta) {
        if (!meta || !meta.href) return;
        const list = load(TOOLS_KEY).filter(t => t.href !== meta.href);
        list.unshift({
            ...meta,
            openedAt: Date.now(),
        });
        save(TOOLS_KEY, list.slice(0, MAX_TOOLS));

        const usage = load(USAGE_KEY);
        const key = meta.href;
        const entry = usage.find(u => u.href === key);
        if (entry) {
            entry.count = (entry.count || 0) + 1;
            entry.lastUsed = Date.now();
        } else {
            usage.push({ href: key, count: 1, lastUsed: Date.now(), ...meta });
        }
        usage.sort((a, b) => b.count - a.count || b.lastUsed - a.lastUsed);
        save(USAGE_KEY, usage.slice(0, 100));
    }

    function trackToolExecuted(meta) {
        trackToolOpen(meta);
    }

    function trackFileProcessed(fileMeta) {
        if (!fileMeta || !fileMeta.name) return;
        const list = load(FILES_KEY).filter(f => f.name !== fileMeta.name || f.toolHref !== fileMeta.toolHref);
        list.unshift({
            name: fileMeta.name,
            size: fileMeta.size || 0,
            toolHref: fileMeta.toolHref || "",
            toolName: fileMeta.toolName || "",
            processedAt: Date.now(),
        });
        save(FILES_KEY, list.slice(0, MAX_FILES));
    }

    function getRecentTools() {
        return load(TOOLS_KEY);
    }

    function getRecentFiles() {
        return load(FILES_KEY);
    }

    function getMostUsed(limit = 6) {
        return load(USAGE_KEY).slice(0, limit);
    }

    function getSuggestedTools(toolIndex, limit = 4) {
        const favorites = typeof Favorites !== "undefined" ? Favorites.getAll() : [];
        const recent = getRecentTools();
        const mostUsed = getMostUsed(limit);
        const seen = new Set();
        const result = [];

        function add(item) {
            const key = item.href || `${item.catId}/${item.toolId}`;
            if (seen.has(key)) return;
            seen.add(key);
            result.push(item);
        }

        favorites.slice(0, 2).forEach(add);
        mostUsed.slice(0, 2).forEach(add);
        recent.slice(0, 2).forEach(add);

        if (result.length < limit && toolIndex) {
            toolIndex.filter(t => !t.disabled).slice(0, limit).forEach(add);
        }
        return result.slice(0, limit);
    }

    function formatRelativeTime(ts) {
        const diff = Date.now() - ts;
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return "Just now";
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        const days = Math.floor(hrs / 24);
        if (days === 1) return "Yesterday";
        return `${days}d ago`;
    }

    function formatSize(bytes) {
        if (!bytes) return "";
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / 1048576).toFixed(1) + " MB";
    }

    function initCurrentPage() {
        const path = window.location.pathname;
        if (path === "/" || path === "/tools" || path === "/settings" || path === "/favorites") return;
        const idx = window.__TOOL_INDEX__ || [];
        const tool = idx.find(t => t.href === path);
        if (tool) {
            trackToolOpen({
                href: tool.href,
                name: tool.name,
                desc: tool.desc,
                icon: tool.icon,
                catId: tool.catId,
                toolId: tool.toolId,
                catName: tool.catName,
            });
        }
    }

    function init() {
        initCurrentPage();
    }

    return {
        trackToolOpen,
        trackToolExecuted,
        trackFileProcessed,
        getRecentTools,
        getRecentFiles,
        getMostUsed,
        getSuggestedTools,
        formatRelativeTime,
        formatSize,
        init,
    };
})();
