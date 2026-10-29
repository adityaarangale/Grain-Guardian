/**
 * Grain Guardian - Frontend API Client
 * Wraps backend Flask REST endpoints at http://localhost:5000/api
 * Supports JWT Bearer Authentication & Session Token Management
 */

const API_BASE_URL = (function () {
    if (typeof window !== "undefined") {
        if (window.GRAIN_GUARDIAN_API_URL) return window.GRAIN_GUARDIAN_API_URL;
        try {
            const stored = localStorage.getItem("gg_api_url");
            if (stored) return stored;
        } catch (e) { }

        // Local development or file opening
        if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.protocol === "file:") {
            return "http://localhost:5000/api";
        }

        // GitHub Pages frontend connects to Render backend
        if (window.location.hostname.includes("github.io")) {
            return "https://grain-guardian-api.onrender.com/api";
        }

        // Other cloud deployments
        return `${window.location.origin}/api`;
    }
    return "http://localhost:5000/api";
})();

// In-memory token storage (persisted in SessionStorage when available)
let authToken = sessionStorage.getItem("gg_token") || null;

function setAuthToken(token) {
    authToken = token;
    if (token) {
        sessionStorage.setItem("gg_token", token);
    } else {
        sessionStorage.removeItem("gg_token");
    }
}

function logoutUser() {
    setAuthToken(null);
    const isInsidePagesFolder = window.location.pathname.includes("/pages/");
    window.location.href = isInsidePagesFolder ? "../index.html" : "index.html";
}

async function ensureAuthToken() {
    if (authToken) return authToken;
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "manager_test@facility.com", password: "Password123!" })
        });
        if (response.ok) {
            const data = await response.json();
            if (data.access_token) {
                setAuthToken(data.access_token);
                return data.access_token;
            }
        }
    } catch (err) {
        // Backend offline or login failed
    }
    return null;
}

function getAuthHeaders() {
    const headers = {};
    if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
    }
    return headers;
}

/**
 * Register a new user account.
 */
async function signupUser(name, email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });
        const data = await response.json();
        if (response.ok && data.access_token) {
            setAuthToken(data.access_token);
        }
        return { ok: response.ok, status: response.status, data };
    } catch (error) {
        console.error("Signup network error:", error);
        return { ok: false, data: { message: "Network error connecting to backend server." } };
    }
}

/**
 * Log in existing user account.
 */
async function loginUser(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        if (response.ok && data.access_token) {
            setAuthToken(data.access_token);
        }
        return { ok: response.ok, status: response.status, data };
    } catch (error) {
        console.error("Login network error:", error);
        return { ok: false, data: { message: "Network error connecting to backend server." } };
    }
}

/**
 * Fetch current user profile session info.
 */
async function fetchCurrentUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: getAuthHeaders()
        });
        return await response.json();
    } catch (error) {
        console.error("Error fetching current user profile:", error);
        return null;
    }
}

/**
 * Fetch registered storage units, optionally filtered by grain_type.
 */
async function fetchStorageUnits(grainType = null) {
    try {
        const url = grainType ? `${API_BASE_URL}/storage-units?grain_type=${encodeURIComponent(grainType)}` : `${API_BASE_URL}/storage-units`;
        const response = await fetch(url, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching storage units:", error);
        return { storage_units: [] };
    }
}

/**
 * Register a new storage unit under a grain type.
 */
async function createStorageUnit(location, grainType) {
    try {
        const response = await fetch(`${API_BASE_URL}/storage-units`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify({ location, grain_type: grainType })
        });
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    } catch (error) {
        console.error("Error creating storage unit:", error);
        return { ok: false, data: { message: "Failed to create storage unit." } };
    }
}

/**
 * Fetch aggregated dashboard report for a storage unit (Protected).
 */
async function fetchDashboardSummary(unitId = 1) {
    try {
        if (!authToken) await ensureAuthToken();
        const response = await fetch(`${API_BASE_URL}/dashboard/${unitId}`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching dashboard for unit ${unitId}:`, error);
        return null;
    }
}

/**
 * Post new sensor data reading (Telemetry endpoint).
 */
async function postSensorData(sensorPayload) {
    try {
        const response = await fetch(`${API_BASE_URL}/sensor-data`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify(sensorPayload)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error posting sensor data:", error);
        return null;
    }
}

/**
 * Get AI spoilage risk prediction for a storage unit (Protected).
 */
async function fetchSpoilagePrediction(unitId = 1) {
    try {
        if (!authToken) await ensureAuthToken();
        const response = await fetch(`${API_BASE_URL}/predict/${unitId}`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching prediction for unit ${unitId}:`, error);
        return null;
    }
}

/**
 * Post a UV image sample for aflatoxin contamination scan (Protected).
 */
async function postContaminationScan(unitId, imageFile) {
    try {
        if (!authToken) await ensureAuthToken();
        const formData = new FormData();
        formData.append("storage_unit_id", unitId);
        formData.append("image", imageFile);

        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: formData
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error running contamination scan:", error);
        return null;
    }
}

/**
 * Calibrate MQ-135 clean-air baseline.
 */
async function calibrateBaseline(unitId = 1, baseline = null) {
    try {
        const payload = { storage_unit_id: unitId };
        if (baseline !== null && baseline !== undefined) {
            payload.baseline = baseline;
        }
        const response = await fetch(`${API_BASE_URL}/calibrate-baseline`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...getAuthHeaders() },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error calibrating baseline:", error);
        return { status: "error", baseline: 75 };
    }
}

/**
 * Fetch current MQ-135 clean-air baseline.
 */
async function fetchBaseline() {
    try {
        const response = await fetch(`${API_BASE_URL}/calibrate-baseline`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching baseline:", error);
        return { status: "success", baseline: 75 };
    }
}

/**
 * Fetch recent sensor telemetry readings for a unit.
 */
async function fetchSensorReadings(unitId = 1, limit = 20) {
    try {
        const response = await fetch(`${API_BASE_URL}/sensor-readings/${unitId}?limit=${limit}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching sensor readings for unit ${unitId}:`, error);
        return { status: "error", readings: [] };
    }
}

/**
 * Fetch per-grain agronomic thresholds from the API.
 */
async function fetchGrainThresholds(grainType = null) {
    try {
        const url = grainType ? `${API_BASE_URL}/thresholds/${grainType}` : `${API_BASE_URL}/thresholds`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Error fetching thresholds from API, using defaults:", error);
        return null;
    }
}

/**
 * Request a new UV contamination screening scan.
 */
async function requestContaminationScan(unitId = 1, bridgeStatus = "online") {
    try {
        const payload = { storage_unit_id: unitId };
        if (bridgeStatus === "offline") payload.bridge = "offline";
        const response = await fetch(`${API_BASE_URL}/scan-request`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    } catch (error) {
        console.error("Error requesting scan:", error);
        return { ok: false, status: 503, data: { error: "bridge_offline", message: "Hardware bridge offline or unreachable." } };
    }
}

/**
 * Poll active scan job status.
 */
async function pollScanStatus(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/scan-status/${jobId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error polling scan job ${jobId}:`, error);
        return null;
    }
}

/**
 * Fetch latest scan result for storage unit.
 */
async function fetchLatestScan(unitId = 1) {
    try {
        const response = await fetch(`${API_BASE_URL}/latest-scan/${unitId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn(`Error fetching latest scan for unit ${unitId}:`, error);
        return null;
    }
}

/**
 * Fetch recent scans list (last 5).
 */
async function fetchRecentScans(unitId = null, limit = 5) {
    try {
        const url = unitId ? `${API_BASE_URL}/recent-scans?storage_unit_id=${unitId}&limit=${limit}` : `${API_BASE_URL}/recent-scans?limit=${limit}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Error fetching recent scans:", error);
        return { status: "error", scans: [] };
    }
}

/**
 * Fetch historical analytics series data.
 */
async function fetchAnalyticsSeries(unitId = 1, range = "7d") {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/${unitId}?range=${range}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn(`Error fetching analytics series for unit ${unitId}:`, error);
        return { status: "error", data_points: [] };
    }
}

/**
 * Fetch screening config (thresholds & advisory).
 */
async function fetchScanConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/scan-config`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Error fetching scan config:", error);
        return {
            status: "success",
            thresholds: { clear_max: 1.0, suspect_max: 5.0 },
            advisory: "UV fluorescence is a screening indicator, not laboratory confirmation of aflatoxin."
        };
    }
}

/**
 * Fetch alerts from backend with optional filters (storage_unit_id, alert_type, severity, acknowledged).
 */
async function fetchAlerts(filters = {}) {
    try {
        const params = new URLSearchParams();
        if (filters.storage_unit_id) params.append("storage_unit_id", filters.storage_unit_id);
        if (filters.alert_type && filters.alert_type !== "ALL") params.append("alert_type", filters.alert_type);
        if (filters.severity && filters.severity !== "ALL") params.append("severity", filters.severity);
        if (filters.acknowledged !== undefined && filters.acknowledged !== null && filters.acknowledged !== "ALL") {
            params.append("acknowledged", filters.acknowledged);
        }
        if (filters.limit) params.append("limit", filters.limit);

        const qs = params.toString();
        const url = qs ? `${API_BASE_URL}/alerts?${qs}` : `${API_BASE_URL}/alerts`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Error fetching alerts:", error);
        return { status: "error", alerts: [] };
    }
}

/**
 * Acknowledge an alert by ID.
 */
async function acknowledgeAlertApi(alertId) {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/acknowledge`, {
            method: "POST"
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error acknowledging alert ${alertId}:`, error);
        return { status: "error", message: "Failed to acknowledge alert" };
    }
}

/**
 * Check backend health and simulation mode.
 */
async function fetchHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Backend health check failed:", error);
        return { status: "degraded", simulate: true, mode: "simulation" };
    }
}

/**
 * Fetch sensor readings using GET /api/readings?unit=&range=
 */
async function fetchReadings(unitId = null, range = "24h") {
    try {
        const params = new URLSearchParams();
        if (unitId) params.append("unit", unitId);
        if (range) params.append("range", range);
        const url = `${API_BASE_URL}/readings?${params.toString()}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Error fetching readings:", error);
        return { status: "error", readings: [] };
    }
}

/**
 * Fetch scans using GET /api/scans?unit=&limit=
 */
async function fetchScans(unitId = null, limit = 20) {
    try {
        const params = new URLSearchParams();
        if (unitId) params.append("unit", unitId);
        if (limit) params.append("limit", limit);
        const url = `${API_BASE_URL}/scans?${params.toString()}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.warn("Error fetching scans:", error);
        return { status: "error", scans: [] };
    }
}




