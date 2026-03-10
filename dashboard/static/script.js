let channelsData = [];
let pipelinesData = [];
let summaryData = [];
let currentTab = "channels";
let sortConfig = { key: null, direction: "asc" };

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initSortableHeaders();
    initTheme();
    refreshAll();
});

function initTheme() {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark");
        document.getElementById("theme-btn").textContent = "☀️";
    }
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    const isDark = document.body.classList.contains("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    document.getElementById("theme-btn").textContent = isDark ? "☀️" : "🌙";
}

function initTabs() {
    const tabs = document.querySelectorAll(".tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            document.getElementById(tab.dataset.tab).classList.add("active");

            currentTab = tab.dataset.tab;
            updateCount();
            filterTable();
        });
    });
}

function initSortableHeaders() {
    document.querySelectorAll("th[data-sort]").forEach(th => {
        th.addEventListener("click", () => {
            const key = th.dataset.sort;
            if (sortConfig.key === key) {
                sortConfig.direction = sortConfig.direction === "asc" ? "desc" : "asc";
            } else {
                sortConfig.key = key;
                sortConfig.direction = "asc";
            }
            updateSortIndicators();
            renderAll();
        });
    });
}

function updateSortIndicators() {
    document.querySelectorAll("th[data-sort]").forEach(th => {
        th.classList.remove("sort-asc", "sort-desc");
        if (th.dataset.sort === sortConfig.key) {
            th.classList.add(sortConfig.direction === "asc" ? "sort-asc" : "sort-desc");
        }
    });
}

function showLoading(show) {
    document.getElementById("loading").style.display = show ? "block" : "none";
}

function showError(msg) {
    const el = document.getElementById("error");
    if (msg) {
        el.textContent = msg;
        el.style.display = "block";
        setTimeout(() => el.style.display = "none", 5000);
    } else {
        el.style.display = "none";
    }
}

let statsData = {};

let historyData = [];
let logsData = [];

async function refreshAll() {
    showLoading(true);
    showError("");

    try {
        const [channelsRes, pipelinesRes, summaryRes, statsRes, historyRes, logsRes] = await Promise.all([
            fetch("/api/channels"),
            fetch("/api/pipelines"),
            fetch("/api/summary"),
            fetch("/api/stats"),
            fetch("/api/history"),
            fetch("/api/logs")
        ]);

        channelsData = await channelsRes.json();
        pipelinesData = await pipelinesRes.json();
        summaryData = await summaryRes.json();
        statsData = await statsRes.json();
        historyData = await historyRes.json();
        logsData = await logsRes.json();

        renderAll();
        document.getElementById("last-updated").textContent = `Updated: ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        showError("Failed to fetch data: " + err.message);
    } finally {
        showLoading(false);
    }
}

function renderAll() {
    renderStats();
    renderChannels();
    renderPipelines();
    renderSummary();
    renderHistory();
    renderLogs();
    updateCount();
    filterTable();
}

function renderHistory() {
    const container = document.getElementById("history-container");
    if (!historyData.length) {
        container.innerHTML = "<p>No history available</p>";
        return;
    }
    container.innerHTML = historyData.map(h => `
        <div class="history-item ${h.runs.some(r => r.type === 'error') ? 'error' : ''}">
            <div class="history-pipeline">${escapeHtml(h.pipeline)}</div>
            ${h.runs.map(r => `
                <div class="history-run ${r.type}">
                    <span>${escapeHtml(r.timestamp)}</span> - ${escapeHtml(r.message)}
                </div>
            `).join("")}
        </div>
    `).join("");
}

function renderLogs() {
    const container = document.getElementById("logs-container");
    if (!logsData.length) {
        container.innerHTML = "<p>No logs available</p>";
        return;
    }
    container.innerHTML = logsData.map(l => `
        <div class="log-item">
            <div class="log-pipeline">${escapeHtml(l.pipeline)}</div>
            <div class="log-lines">${escapeHtml(l.lines.join("\n"))}</div>
        </div>
    `).join("");
}

function renderStats() {
    if (!statsData.total_pipelines) return;
    document.getElementById("stat-total-pipelines").textContent = statsData.total_pipelines;
    document.getElementById("stat-enabled-pipelines").textContent = statsData.enabled_pipelines;
    document.getElementById("stat-disabled-pipelines").textContent = statsData.disabled_pipelines;
    document.getElementById("stat-total-channels").textContent = statsData.total_channels;
    document.getElementById("stat-total-members").textContent = statsData.total_members.toLocaleString();
    document.getElementById("stat-public-channels").textContent = statsData.public_channels;
}

function sortData(data, key, direction) {
    if (!key) return data;
    return [...data].sort((a, b) => {
        let aVal = a[key];
        let bVal = b[key];
        if (aVal == null) aVal = "";
        if (bVal == null) bVal = "";
        if (typeof aVal === "number" && typeof bVal === "number") {
            return direction === "asc" ? aVal - bVal : bVal - aVal;
        }
        aVal = String(aVal).toLowerCase();
        bVal = String(bVal).toLowerCase();
        if (direction === "asc") {
            return aVal.localeCompare(bVal);
        }
        return bVal.localeCompare(aVal);
    });
}

function renderChannels() {
    const sorted = sortData(channelsData, sortConfig.key, sortConfig.direction);
    const tbody = document.querySelector("#channels-table tbody");
    tbody.innerHTML = sorted.map(ch => `
        <tr>
            <td>${escapeHtml(ch.title)}</td>
            <td>${escapeHtml(String(ch.id))}</td>
            <td>${ch.invite_link ? `<a href="${escapeHtml(ch.invite_link)}" target="_blank">Link</a>` : "-"}</td>
            <td class="${ch.is_public ? "enabled" : "disabled"}" data-sort-value="${ch.is_public ? 1 : 0}">${ch.is_public ? "Yes" : "No"}</td>
            <td data-sort-value="${ch.member_count ?? -1}">${ch.member_count !== null ? ch.member_count.toLocaleString() : "-"}</td>
            <td>${escapeHtml(ch.type || "-")}</td>
            <td>${escapeHtml(truncate(ch.description, 100))}</td>
        </tr>
    `).join("");
}

function renderPipelines() {
    const sorted = sortData(pipelinesData, sortConfig.key, sortConfig.direction);
    const tbody = document.querySelector("#pipelines-table tbody");
    tbody.innerHTML = sorted.map(p => `
        <tr>
            <td>${escapeHtml(p.name)}</td>
            <td class="${p.enabled ? "enabled" : "disabled"}" data-sort-value="${p.enabled ? 1 : 0}">${p.enabled ? "Yes" : "No"}</td>
            <td>${formatSource(p.source)}</td>
            <td>${escapeHtml(p.target_channel || "-")}</td>
            <td data-sort-value="${p.run_every_minutes ?? -1}">${p.run_every_minutes ? p.run_every_minutes + " min" : "-"}</td>
        </tr>
    `).join("");
}

function renderSummary() {
    const sorted = sortData(summaryData, sortConfig.key, sortConfig.direction);
    const tbody = document.querySelector("#summary-table tbody");
    tbody.innerHTML = sorted.map(s => `
        <tr>
            <td>
                <strong>${escapeHtml(s.title)}</strong><br>
                <small>${escapeHtml(String(s.id))}</small>
            </td>
            <td data-sort-value="${s.member_count ?? -1}">${s.member_count !== null ? s.member_count.toLocaleString() : "-"}</td>
            <td class="pipelines-cell">
                ${(s.pipelines || []).map(p => `<span class="pipeline-tag">${escapeHtml(p)}</span>`).join("")}
            </td>
        </tr>
    `).join("");
}

function updateCount() {
    if (currentTab === "stats" || currentTab === "history" || currentTab === "logs") {
        document.getElementById("count").textContent = "";
        return;
    }
    let count = 0;
    if (currentTab === "channels") count = channelsData.length;
    else if (currentTab === "pipelines") count = pipelinesData.length;
    else if (currentTab === "summary") count = summaryData.length;
    document.getElementById("count").textContent = `Total: ${count}`;
}

function filterTable() {
    const query = document.getElementById("search").value.toLowerCase();
    let selector = "";

    if (currentTab === "channels") selector = "#channels-table tbody tr";
    else if (currentTab === "pipelines") selector = "#pipelines-table tbody tr";
    else if (currentTab === "summary") selector = "#summary-table tbody tr";

    document.querySelectorAll(selector).forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
    });
}

function formatSource(source) {
    if (!source) return "-";
    const task = source.task || "";
    const taskName = task.split(".").pop() || "";
    const tags = source.redgifs?.tags || source.reddit?.subreddit || "-";
    return `${taskName} (${tags})`;
}

function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function truncate(str, len) {
    if (!str) return "";
    return str.length > len ? str.substring(0, len) + "..." : str;
}
