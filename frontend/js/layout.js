/**
 * Grain Guardian - Unified Layout Injector & UI Component System
 * Injects identical 260px Sidebar, 64px Topbar, Global Selects, Status Chip, and Add Unit Modal.
 * Replaces all icon ligatures with inline SVG icons to eliminate broken text.
 */

(function (global) {
    // High-precision inline SVG icons - zero external webfont dependency
    const GGIcons = {
        brand: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M12 2v20M7 7l5-5 5 5M4 14l8-8 8 8M2 20l10-10 10 10"/></svg>`,
        dashboard: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>`,
        storage: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>`,
        ai: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>`,
        scan: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></svg>`,
        analytics: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>`,
        alerts: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>`,
        logout: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
        chevronDown: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="m6 9 6 6 6-6"/></svg>`,
        plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M5 12h14M12 5v14"/></svg>`,
        close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M18 6 6 18M6 6l12 12"/></svg>`,
        refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>`,
        upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
        
        // Risk Status Icons
        safe: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
        medium: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
        high: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
        critical: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,

        // Telemetry Metrics Icons
        temp: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg>`,
        humidity: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`,
        gas: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>`,
        moisture: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
        fan: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gg-icon"><circle cx="12" cy="12" r="10"/><path d="M14.31 8 20.05 17.94"/><path d="M9.69 8h11.48"/><path d="m7.38 12 5.74-9.94"/><path d="M9.69 16 3.95 6.06"/><path d="M14.31 16H2.83"/><path d="m16.62 12-5.74 9.94"/></svg>`
    };

    // Standardized Navigation & Page Meta Definition
    const NAV_ITEMS = [
        { id: "dashboard", href: "dashboard.html", label: "Dashboard", title: "Dashboard", subtitle: "Facility overview", icon: GGIcons.dashboard },
        { id: "storage-monitoring", href: "storage-monitoring.html", label: "Storage Monitoring", title: "Storage Monitoring", subtitle: "Live sensor readings", icon: GGIcons.storage },
        { id: "ai-prediction", href: "ai-prediction.html", label: "AI Prediction", title: "AI Prediction", subtitle: "Spoilage risk and safe storage days", icon: GGIcons.ai },
        { id: "contamination-scan", href: "contamination-scan.html", label: "Contamination Scan", title: "Contamination Scan", subtitle: "UV fluorescence screening", icon: GGIcons.scan },
        { id: "analytics", href: "analytics.html", label: "Analytics", title: "Analytics", subtitle: "Historical trends", icon: GGIcons.analytics },
        { id: "alerts", href: "alerts.html", label: "Alerts", title: "Alerts", subtitle: "Alert history", icon: GGIcons.alerts }
    ];

    /**
     * Standardizes Risk Badge HTML.
     * Allowed output values ONLY: Safe, Medium, High, Critical (Removes "Low Risk" or trailing "Risk").
     */
    function getRiskBadgeHtml(risk) {
        if (!risk) risk = "Safe";
        const clean = String(risk).trim().toLowerCase();
        let normalized = "Safe";
        let icon = GGIcons.safe;

        if (clean === "low" || clean === "low risk" || clean === "safe") {
            normalized = "Safe";
            icon = GGIcons.safe;
        } else if (clean === "medium" || clean === "medium risk") {
            normalized = "Medium";
            icon = GGIcons.medium;
        } else if (clean === "high" || clean === "high risk") {
            normalized = "High";
            icon = GGIcons.high;
        } else if (clean === "critical" || clean === "critical risk") {
            normalized = "Critical";
            icon = GGIcons.critical;
        }

        const cls = `risk-badge risk-badge-${normalized.toLowerCase()}`;
        return `<span class="${cls}">${icon} <span>${normalized}</span></span>`;
    }

    /**
     * Determines the active page ID from the current pathname or explicit configuration.
     */
    function detectActivePage(explicitId) {
        if (explicitId) return explicitId;
        const path = window.location.pathname.toLowerCase();
        for (const item of NAV_ITEMS) {
            if (path.includes(item.href.toLowerCase()) || path.endsWith("/" + item.id)) {
                return item.id;
            }
        }
        return "dashboard";
    }

    /**
     * Main Unified Layout Initializer.
     * Injects the fixed Sidebar, sticky Topbar, and wraps content area.
     */
    async function initPageLayout(options = {}) {
        const activeNavId = detectActivePage(options.activeNav);
        const currentMeta = NAV_ITEMS.find(n => n.id === activeNavId) || NAV_ITEMS[0];
        
        const title = options.title || currentMeta.title;
        const subtitle = options.subtitle || currentMeta.subtitle;

        // Existing page content element
        let pageContentElem = document.getElementById("page-content") || document.querySelector("main");
        const existingContentHtml = pageContentElem ? pageContentElem.innerHTML : "";

        // Build Nav Links HTML
        const navLinksHtml = NAV_ITEMS.map(item => {
            const isActive = item.id === activeNavId;
            const activeClass = isActive ? "nav-item active" : "nav-item";
            return `
                <a href="${item.href}" class="${activeClass}" id="nav-link-${item.id}">
                    ${item.icon}
                    <span>${item.label}</span>
                </a>
            `;
        }).join("");

        // Build Grain Dropdown Options
        const selectedGrain = GrainState.getSelectedGrain();
        const grainOptionsHtml = GrainState.VALID_GRAINS.map(g => {
            const isSel = g === selectedGrain ? "selected" : "";
            return `<option value="${g}" ${isSel}>${g}</option>`;
        }).join("");

        // Build Demo Badge
        const isSimulate = GrainState.isSimulateMode();
        const demoBadgeHtml = `
            <div id="topbar-demo-badge" class="demo-badge" style="${isSimulate ? '' : 'display: none;'}">
                Demo data
            </div>
        `;

        // Compose Full App HTML Shell
        const layoutHtml = `
            <div id="app-root">
                <!-- Fixed 260px Full-Height Sidebar -->
                <aside class="app-sidebar" aria-label="Main Navigation">
                    <div class="sidebar-header">
                        <a href="dashboard.html" class="sidebar-brand">
                            <span class="sidebar-brand-icon">${GGIcons.brand}</span>
                            <span>Grain Guardian</span>
                        </a>
                    </div>
                    <nav class="sidebar-nav">
                        ${navLinksHtml}
                    </nav>
                    <div class="sidebar-footer">
                        <button type="button" class="logout-btn" onclick="logoutUser()">
                            ${GGIcons.logout}
                            <span>Logout</span>
                        </button>
                    </div>
                </aside>

                <!-- Main Application Container -->
                <div class="app-main">
                    <!-- Sticky 64px Topbar -->
                    <header class="app-topbar">
                        <div class="topbar-left">
                            <h1 class="topbar-title" id="page-title">${title}</h1>
                            <p class="topbar-subtitle" id="page-subtitle">${subtitle}</p>
                        </div>
                        <div class="topbar-right">
                            ${demoBadgeHtml}

                            <!-- Grain Select -->
                            <div class="select-group">
                                <label for="header-grain-select" class="select-label">Grain</label>
                                <div class="select-container">
                                    <select id="header-grain-select" class="theme-select">
                                        ${grainOptionsHtml}
                                    </select>
                                    <div class="select-chevron">${GGIcons.chevronDown}</div>
                                </div>
                            </div>

                            <!-- Storage Unit Select -->
                            <div class="select-group">
                                <label for="header-unit-select" class="select-label">Unit</label>
                                <div class="select-container">
                                    <select id="header-unit-select" class="theme-select">
                                        <option value="" disabled selected>Loading units...</option>
                                    </select>
                                    <div class="select-chevron">${GGIcons.chevronDown}</div>
                                </div>
                            </div>

                            <!-- Add Unit Quick Button -->
                            <button type="button" id="header-add-unit-btn" class="btn-primary btn-sm" title="Register New Storage Unit">
                                ${GGIcons.plus}
                                <span>Add unit</span>
                            </button>

                            <!-- System Status Chip -->
                            <div id="system-status-chip" class="status-chip live" title="Backend API connection status">
                                <span class="status-dot"></span>
                                <span id="system-status-text">Live</span>
                            </div>
                        </div>
                    </header>

                    <!-- Content Canvas (1400px Max-Width, 32px Padding) -->
                    <main class="content-area" id="page-content">
                        ${existingContentHtml}
                    </main>
                </div>
            </div>

            <!-- Global Modal: Add Storage Unit -->
            <div id="add-unit-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 class="modal-title">Register Storage Unit</h2>
                        <button type="button" class="modal-close-btn" onclick="GrainLayout.closeAddUnitModal()">
                            ${GGIcons.close}
                        </button>
                    </div>
                    <form id="add-unit-form" onsubmit="GrainLayout.handleAddUnitSubmit(event)">
                        <div class="form-field">
                            <label class="form-label" for="new-unit-grain">Grain Type</label>
                            <input type="text" id="new-unit-grain" class="form-input" readonly disabled />
                        </div>
                        <div class="form-field">
                            <label class="form-label" for="new-unit-location">Facility / Location Identifier</label>
                            <input type="text" id="new-unit-location" class="form-input" placeholder="e.g. Silo B-2, Warehouse 4" required />
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn-outline" onclick="GrainLayout.closeAddUnitModal()">Cancel</button>
                            <button type="submit" class="btn-primary" id="save-unit-submit-btn">Save Unit</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.innerHTML = layoutHtml;

        // Wire Up Event Handlers
        attachLayoutEvents();

        // Load Storage Units for Current Grain
        await syncStorageUnitsDropdown();

        // Check backend health for Live/Offline indicator
        checkBackendHealth();
    }

    /**
     * Wires layout events (Grain select, Unit select, Simulation toggle, Add unit button).
     */
    function attachLayoutEvents() {
        const grainSelect = document.getElementById("header-grain-select");
        const unitSelect = document.getElementById("header-unit-select");
        const addBtn = document.getElementById("header-add-unit-btn");
        const simBtn = document.getElementById("toggle-simulate-btn");

        if (grainSelect) {
            grainSelect.addEventListener("change", async (e) => {
                const newGrain = e.target.value;
                GrainState.setSelectedGrain(newGrain, false);
                await syncStorageUnitsDropdown();
                GrainState.notify({ type: "grain", grain: newGrain });
            });
        }

        if (unitSelect) {
            unitSelect.addEventListener("change", (e) => {
                const val = e.target.value;
                if (val === "ADD_NEW_UNIT") {
                    openAddUnitModal();
                    // Reset dropdown to active
                    unitSelect.value = GrainState.getSelectedUnitId() || "";
                } else if (val) {
                    const unitId = parseInt(val, 10);
                    GrainState.setSelectedUnitId(unitId, true);
                }
            });
        }

        if (addBtn) {
            addBtn.addEventListener("click", () => openAddUnitModal());
        }

        // Keep topbar selects in sync when state changes from elsewhere (e.g., clicking table row)
        GrainState.onStateChange(async (detail) => {
            const gSel = document.getElementById("header-grain-select");
            const uSel = document.getElementById("header-unit-select");
            const curGrain = GrainState.getSelectedGrain();
            const curUnit = GrainState.getSelectedUnitId();

            if (gSel && gSel.value !== curGrain) {
                gSel.value = curGrain;
                await syncStorageUnitsDropdown();
            }
            if (uSel && curUnit !== null && uSel.value !== String(curUnit)) {
                uSel.value = String(curUnit);
            }
        });
    }

    /**
     * Fetches storage units matching current selectedGrain from API, populating dropdown.
     */
    async function syncStorageUnitsDropdown() {
        const grain = GrainState.getSelectedGrain();
        const unitSelect = document.getElementById("header-unit-select");
        const addBtn = document.getElementById("header-add-unit-btn");

        if (!unitSelect) return;

        unitSelect.innerHTML = `<option value="" disabled selected>Loading...</option>`;

        let units = [];
        try {
            if (typeof fetchStorageUnits === "function") {
                const res = await fetchStorageUnits(grain.toLowerCase());
                if (res && Array.isArray(res.storage_units)) {
                    units = res.storage_units;
                }
            }
        } catch (err) {
            console.warn("Could not fetch units from API:", err);
        }

        // If in simulation mode and API has 0 units, provide sample unit options
        if (units.length === 0 && GrainState.isSimulateMode()) {
            units = [
                { id: 101, location: `Silo 1 (${grain})`, grain_type: grain.toLowerCase() },
                { id: 102, location: `Bin A-4 (${grain})`, grain_type: grain.toLowerCase() }
            ];
        }

        if (units.length > 0) {
            unitSelect.disabled = false;
            let currentUnitId = GrainState.getSelectedUnitId();
            
            // Check if currentUnitId exists in this grain's units
            const exists = units.some(u => u.id === currentUnitId);
            if (!exists) {
                currentUnitId = units[0].id;
                GrainState.setSelectedUnitId(currentUnitId, false);
            }

            const optionsHtml = units.map(u => {
                const isSel = u.id === currentUnitId ? "selected" : "";
                return `<option value="${u.id}" ${isSel}>${u.location}</option>`;
            }).join("");

            unitSelect.innerHTML = optionsHtml;
        } else {
            // Requirement 5: "If there are no units, show a disabled "No units yet" and an "Add unit" button."
            unitSelect.disabled = true;
            unitSelect.innerHTML = `<option value="" disabled selected>No units yet</option>`;
            GrainState.setSelectedUnitId(null, false);
        }
    }

    /**
     * Checks if backend API is reachable and updates Live/Offline chip and Demo data badge.
     */
    async function checkBackendHealth() {
        const chip = document.getElementById("system-status-chip");
        const text = document.getElementById("system-status-text");
        const badge = document.getElementById("topbar-demo-badge");
        if (!chip || !text) return;

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2500);
            const res = await fetch("http://localhost:5000/api/health", { signal: controller.signal });
            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                chip.className = "status-chip live";
                text.textContent = "Live";

                // Requirement 4: Frontend shows a "Demo data" badge only when the API reports simulate mode
                const isSim = Boolean(data.simulate);
                GrainState.setSimulateMode(isSim);
                if (badge) {
                    badge.style.display = isSim ? "inline-flex" : "none";
                }
            } else {
                chip.className = "status-chip offline";
                text.textContent = "Offline";
                if (badge) badge.style.display = "none";
            }
        } catch (e) {
            chip.className = "status-chip offline";
            text.textContent = "Offline";
            if (badge) badge.style.display = "none";
        }
    }

    function openAddUnitModal() {
        const modal = document.getElementById("add-unit-modal");
        const grainInput = document.getElementById("new-unit-grain");
        const locInput = document.getElementById("new-unit-location");
        if (!modal) return;

        const grain = GrainState.getSelectedGrain();
        if (grainInput) grainInput.value = grain;
        if (locInput) {
            locInput.value = "";
            setTimeout(() => locInput.focus(), 50);
        }
        modal.style.display = "flex";
    }

    function closeAddUnitModal() {
        const modal = document.getElementById("add-unit-modal");
        if (modal) modal.style.display = "none";
    }

    async function handleAddUnitSubmit(e) {
        e.preventDefault();
        const locInput = document.getElementById("new-unit-location");
        const location = locInput ? locInput.value.trim() : "";
        const grain = GrainState.getSelectedGrain();

        if (!location) return;

        const submitBtn = document.getElementById("save-unit-submit-btn");
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Saving...";
        }

        try {
            let newId = null;
            if (typeof createStorageUnit === "function") {
                const res = await createStorageUnit(location, grain.toLowerCase());
                if (res && res.ok && res.data && res.data.id) {
                    newId = res.data.id;
                }
            }

            if (!newId) {
                // Fallback ID if offline or mock
                newId = Date.now() % 10000;
            }

            closeAddUnitModal();
            GrainState.setSelectedUnitId(newId, false);
            await syncStorageUnitsDropdown();
            GrainState.notify({ type: "unit", unitId: newId });
        } catch (err) {
            console.error("Failed to create unit:", err);
            alert("Could not register storage unit. Please check backend connection.");
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = "Save Unit";
            }
        }
    }

    // Export Layout Helpers to Global
    global.GrainLayout = {
        init: initPageLayout,
        getRiskBadgeHtml,
        openAddUnitModal,
        closeAddUnitModal,
        handleAddUnitSubmit,
        syncStorageUnitsDropdown,
        icons: GGIcons
    };

})(typeof window !== "undefined" ? window : this);
