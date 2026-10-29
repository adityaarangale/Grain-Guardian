/**
 * Grain Guardian - Global State Manager
 * Persists selectedGrain and selectedUnitId across pages via localStorage with safe try/catch.
 * Grain list is strictly: Wheat, Rice, Maize, Groundnut, Pulses (Yellow Corn is renamed to Maize).
 */

(function (global) {
    const STORAGE_KEY_GRAIN = "gg_selected_grain";
    const STORAGE_KEY_UNIT = "gg_selected_unit_id";
    const STORAGE_KEY_SIMULATE = "gg_simulate_mode";

    // Strictly validated grain list
    const VALID_GRAINS = ["Wheat", "Rice", "Maize", "Groundnut", "Pulses"];

    // In-memory fallback if localStorage is disabled or throws
    const memoryStore = {
        selectedGrain: "Wheat",
        selectedUnitId: null,
        simulateMode: false
    };

    function safeGet(key, fallback = null) {
        try {
            if (typeof window !== "undefined" && window.localStorage) {
                const val = window.localStorage.getItem(key);
                return val !== null ? val : fallback;
            }
        } catch (err) {
            console.warn(`localStorage read error for key "${key}":`, err);
        }
        return fallback;
    }

    function safeSet(key, value) {
        try {
            if (typeof window !== "undefined" && window.localStorage) {
                if (value === null || value === undefined) {
                    window.localStorage.removeItem(key);
                } else {
                    window.localStorage.setItem(key, String(value));
                }
            }
        } catch (err) {
            console.warn(`localStorage write error for key "${key}":`, err);
        }
    }

    function normalizeGrain(grain) {
        if (!grain) return "Wheat";
        const clean = String(grain).trim().toLowerCase();
        if (clean === "yellow corn" || clean === "corn") return "Maize";
        
        for (const valid of VALID_GRAINS) {
            if (valid.toLowerCase() === clean) {
                return valid;
            }
        }
        return "Wheat";
    }

    const GrainState = {
        VALID_GRAINS: [...VALID_GRAINS],

        getSelectedGrain() {
            const raw = safeGet(STORAGE_KEY_GRAIN, memoryStore.selectedGrain);
            const normalized = normalizeGrain(raw);
            if (raw !== normalized) {
                this.setSelectedGrain(normalized, false);
            }
            return normalized;
        },

        setSelectedGrain(grain, notify = true) {
            const normalized = normalizeGrain(grain);
            memoryStore.selectedGrain = normalized;
            safeSet(STORAGE_KEY_GRAIN, normalized);
            if (notify) {
                this.notify({ type: "grain", grain: normalized });
            }
        },

        getSelectedUnitId() {
            const raw = safeGet(STORAGE_KEY_UNIT, memoryStore.selectedUnitId);
            if (raw === null || raw === undefined || raw === "") {
                return null;
            }
            const parsed = parseInt(raw, 10);
            return isNaN(parsed) ? null : parsed;
        },

        setSelectedUnitId(unitId, notify = true) {
            const val = unitId ? parseInt(unitId, 10) : null;
            memoryStore.selectedUnitId = val;
            safeSet(STORAGE_KEY_UNIT, val !== null ? val : "");
            if (notify) {
                this.notify({ type: "unit", unitId: val });
            }
        },

        isSimulateMode() {
            const raw = safeGet(STORAGE_KEY_SIMULATE, String(memoryStore.simulateMode));
            return raw === "true";
        },

        setSimulateMode(enabled, notify = true) {
            const boolVal = Boolean(enabled);
            memoryStore.simulateMode = boolVal;
            safeSet(STORAGE_KEY_SIMULATE, String(boolVal));
            if (notify) {
                this.notify({ type: "simulate", simulateMode: boolVal });
            }
        },

        toggleSimulateMode() {
            const next = !this.isSimulateMode();
            this.setSimulateMode(next);
            return next;
        },

        notify(detail) {
            if (typeof window !== "undefined") {
                const event = new CustomEvent("gg:state-change", {
                    detail: {
                        grain: this.getSelectedGrain(),
                        unitId: this.getSelectedUnitId(),
                        simulateMode: this.isSimulateMode(),
                        ...detail
                    }
                });
                window.dispatchEvent(event);
            }
        },

        onStateChange(callback) {
            if (typeof window === "undefined") return () => {};
            
            const handleCustom = (e) => callback(e.detail);
            const handleStorage = (e) => {
                if (e.key === STORAGE_KEY_GRAIN || e.key === STORAGE_KEY_UNIT || e.key === STORAGE_KEY_SIMULATE) {
                    callback({
                        type: "storage-sync",
                        grain: this.getSelectedGrain(),
                        unitId: this.getSelectedUnitId(),
                        simulateMode: this.isSimulateMode()
                    });
                }
            };

            window.addEventListener("gg:state-change", handleCustom);
            window.addEventListener("storage", handleStorage);

            // Return unsubscribe function
            return () => {
                window.removeEventListener("gg:state-change", handleCustom);
                window.removeEventListener("storage", handleStorage);
            };
        }
    };

    // Ensure grain state is normalized at startup
    GrainState.getSelectedGrain();

    global.GrainState = GrainState;
})(typeof window !== "undefined" ? window : this);
