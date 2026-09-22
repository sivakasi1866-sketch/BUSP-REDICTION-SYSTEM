// Partners Bus Prediction - Frontend Application Core
const API_BASE = "/api";

// Application State
const state = {
  token: localStorage.getItem("token") || null,
  user: JSON.parse(localStorage.getItem("user") || "null"),
  currentTab: "dashboard",
  activeTrip: null,
  myBusTracking: null,
  notifications: [],
  map: null,
  busMarker: null,
  routePolyline: null,
  stopMarkers: [],
  gpsWatchId: null,
  gpsSimInterval: null,
  simulatedStepIdx: 0,
  refreshInterval: null
};

// API Client Helper
async function apiCall(endpoint, options = {}) {
  const headers = { ...options.headers };
  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }
  if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    if (res.status === 401) {
      logout();
      throw new Error("Session expired. Please log in again.");
    }
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "API Request Failed");
    }
    return data;
  } catch (err) {
    console.error("API Error:", err);
    throw err;
  }
}

// Authentication Handlers
async function handleLogin(username, password) {
  try {
    const res = await apiCall("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    state.token = res.access_token;
    state.user = {
      id: res.user_id,
      username: res.username,
      full_name: res.full_name,
      role: res.role
    };
    localStorage.setItem("token", state.token);
    localStorage.setItem("user", JSON.stringify(state.user));
    renderApp();
  } catch (err) {
    alert("Login failed: " + err.message);
  }
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  if (state.refreshInterval) clearInterval(state.refreshInterval);
  if (state.gpsSimInterval) clearInterval(state.gpsSimInterval);
  renderApp();
}

function quickLogin(roleName) {
  const credentials = {
    admin: ["admin", "admin123"],
    driver: ["driver1", "driver123"],
    student: ["student1", "student123"],
    staff: ["staff1", "staff123"]
  };
  const [u, p] = credentials[roleName];
  handleLogin(u, p);
}

// Global App Renderer
function renderApp() {
  const appContainer = document.getElementById("app");
  if (!state.user) {
    renderLoginView(appContainer);
  } else if (state.user.role === "ADMIN") {
    renderAdminView(appContainer);
  } else if (state.user.role === "DRIVER") {
    renderDriverView(appContainer);
  } else {
    // STUDENT or STAFF
    renderPassengerView(appContainer);
  }
  updateHeader();
}

// Header Updater
function updateHeader() {
  const navContainer = document.getElementById("header-nav");
  if (!state.user) {
    navContainer.innerHTML = `<span class="badge-cost">Operating Cost: ₹0 / Free-Tier</span>`;
    return;
  }
  navContainer.innerHTML = `
    <span class="badge-cost">Operating Cost: ₹0</span>
    <div class="user-badge">
      <span>${escapeHtml(state.user.full_name)}</span>
      <span class="role-tag">${state.user.role}</span>
    </div>
    <button class="btn btn-outline" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="logout()">Logout</button>
  `;
}

// -------------------------------------------------------------
// 1. LOGIN VIEW
// -------------------------------------------------------------
function renderLoginView(container) {
  container.innerHTML = `
    <div style="max-width: 440px; margin: 3rem auto;">
      <div class="card" style="padding: 2rem;">
        <div style="text-align: center; margin-bottom: 1.5rem;">
          <div class="brand-icon" style="margin: 0 auto 0.75rem; width: 50px; height: 50px; font-size: 1.8rem;">🚌</div>
          <h2 style="font-size: 1.5rem; color: var(--neutral-900);">Partners Bus Prediction</h2>
          <p style="color: var(--neutral-500); font-size: 0.85rem; margin-top: 0.25rem;">Smart College Bus Tracking & ETA Prediction</p>
        </div>

        <form id="login-form" onsubmit="event.preventDefault(); handleLogin(this.username.value, this.password.value);">
          <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" placeholder="e.g. admin, driver1, student1" required>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" placeholder="Enter password" required>
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;">Sign In</button>
        </form>

        <div style="margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid var(--neutral-200);">
          <p style="font-size: 0.8rem; color: var(--neutral-500); margin-bottom: 0.5rem; text-align: center; font-weight: 600;">DEMO ONE-CLICK LOGIN:</p>
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
            <button class="btn btn-outline" style="font-size: 0.8rem;" onclick="quickLogin('admin')">🔑 Admin</button>
            <button class="btn btn-outline" style="font-size: 0.8rem;" onclick="quickLogin('driver')">🚍 Driver</button>
            <button class="btn btn-outline" style="font-size: 0.8rem;" onclick="quickLogin('student')">🎓 Student</button>
            <button class="btn btn-outline" style="font-size: 0.8rem;" onclick="quickLogin('staff')">👨‍🏫 Staff</button>
          </div>
        </div>

        <div style="margin-top: 1.25rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 0.6rem; font-size: 0.75rem; color: #166534; text-align: center;">
          🔒 <strong>Privacy Assured:</strong> Passengers are never tracked. Driver GPS is strictly trip-scoped.
        </div>
      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// 2. ADMIN VIEW
// -------------------------------------------------------------
async function renderAdminView(container) {
  container.innerHTML = `
    <div class="tabs">
      <button class="tab-btn ${state.currentTab === 'dashboard' ? 'active' : ''}" onclick="switchAdminTab('dashboard')">📊 Fleet Dashboard</button>
      <button class="tab-btn ${state.currentTab === 'users' ? 'active' : ''}" onclick="switchAdminTab('users')">👥 User Management</button>
      <button class="tab-btn ${state.currentTab === 'buses' ? 'active' : ''}" onclick="switchAdminTab('buses')">🚌 Bus Fleet</button>
      <button class="tab-btn ${state.currentTab === 'routes' ? 'active' : ''}" onclick="switchAdminTab('routes')">🗺️ Routes & Stops</button>
      <button class="tab-btn ${state.currentTab === 'assignments' ? 'active' : ''}" onclick="switchAdminTab('assignments')">📋 Allocations & Exam Days</button>
      <button class="tab-btn ${state.currentTab === 'reports' ? 'active' : ''}" onclick="switchAdminTab('reports')">📈 ML & Reports</button>
      <button class="tab-btn" onclick="openExcelImportModal()">📥 Excel Bulk Import</button>
    </div>
    <div id="admin-tab-content">
      <div style="text-align: center; padding: 2rem;">Loading fleet information...</div>
    </div>
  `;
  loadAdminTabContent();
}

function switchAdminTab(tabName) {
  state.currentTab = tabName;
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  const clicked = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.textContent.toLowerCase().includes(tabName));
  if (clicked) clicked.classList.add("active");
  loadAdminTabContent();
}

async function loadAdminTabContent() {
  const content = document.getElementById("admin-tab-content");
  if (!content) return;

  if (state.currentTab === "dashboard") {
    try {
      const summary = await apiCall("/reports/dashboard-summary");
      content.innerHTML = `
        <div class="grid-4" style="margin-bottom: 1.25rem;">
          <div class="stat-card">
            <div class="stat-icon">🚌</div>
            <div>
              <div class="stat-value">${summary.fleet.total_buses}</div>
              <div class="stat-label">Total Buses (${summary.fleet.buses_on_trip} Active)</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🚀</div>
            <div>
              <div class="stat-value">${summary.trips.active}</div>
              <div class="stat-label">Active Trips Now</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🎓</div>
            <div>
              <div class="stat-value">${summary.users.students}</div>
              <div class="stat-label">Registered Students</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">👨‍🏫</div>
            <div>
              <div class="stat-value">${summary.users.staff}</div>
              <div class="stat-label">Registered Faculty</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">🗺️ Live Fleet Tracking Map</div>
            <span class="badge-cost">OpenStreetMap Free Tier</span>
          </div>
          <div id="fleet-map" class="map-box"></div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">🕒 Recent Trips & Fleet Status</div>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Trip Name</th>
                  <th>Bus Number</th>
                  <th>Route</th>
                  <th>Driver</th>
                  <th>Status</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                </tr>
              </thead>
              <tbody>
                ${summary.recent_trips.map(t => `
                  <tr>
                    <td><strong>${escapeHtml(t.trip_name)}</strong></td>
                    <td>${escapeHtml(t.bus_number)}</td>
                    <td>${escapeHtml(t.route_name)}</td>
                    <td>${escapeHtml(t.driver_name)}</td>
                    <td>
                      <span class="role-tag" style="background: ${t.status === 'ACTIVE' ? 'var(--success)' : 'var(--neutral-500)'}">
                        ${t.status}
                      </span>
                    </td>
                    <td>${t.start_time}</td>
                    <td>${t.end_time}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
      initFleetMap();
    } catch (err) {
      content.innerHTML = `<div class="card"><p style="color:red">Error loading dashboard: ${err.message}</p></div>`;
    }
  } else if (state.currentTab === "users") {
    loadAdminUsersTab(content);
  } else if (state.currentTab === "buses") {
    loadAdminBusesTab(content);
  } else if (state.currentTab === "routes") {
    loadAdminRoutesTab(content);
  } else if (state.currentTab === "assignments") {
    loadAdminAssignmentsTab(content);
  } else if (state.currentTab === "reports") {
    loadAdminReportsTab(content);
  }
}

// Admin Users Tab
async function loadAdminUsersTab(container) {
  try {
    const users = await apiCall("/users");
    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title">👥 User Directory (${users.length} Users)</div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-primary" onclick="openCreateUserModal()">+ Add New User</button>
            <button class="btn btn-outline" onclick="openExcelImportModal()">📥 Bulk Excel</button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Name / Username</th>
                <th>Role</th>
                <th>Identifier / Roll / EmpID</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${users.map(u => {
                let identifier = "—";
                if (u.student_profile) identifier = `${u.student_profile.roll_number} (${u.student_profile.department})`;
                else if (u.staff_profile) identifier = `${u.staff_profile.employee_id} (${u.staff_profile.department})`;
                else if (u.driver_profile) identifier = `${u.driver_profile.license_number}`;
                
                return `
                  <tr>
                    <td>
                      <strong>${escapeHtml(u.full_name)}</strong><br>
                      <small style="color:var(--neutral-500)">@${escapeHtml(u.username)}</small>
                    </td>
                    <td><span class="role-tag">${u.role}</span></td>
                    <td>${escapeHtml(identifier)}</td>
                    <td>${escapeHtml(u.phone || "—")}</td>
                    <td>${u.is_active ? '<span style="color:var(--success)">Active</span>' : '<span style="color:var(--danger)">Inactive</span>'}</td>
                    <td>
                      ${u.is_active ? `<button class="btn btn-outline" style="padding:0.2rem 0.5rem; font-size:0.75rem; color:var(--danger)" onclick="deactivateUser(${u.id})">Deactivate</button>` : '—'}
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:red">Error loading users: ${err.message}</p>`;
  }
}

async function deactivateUser(id) {
  if (!confirm("Are you sure you want to deactivate this user account?")) return;
  try {
    await apiCall(`/users/${id}`, { method: "DELETE" });
    loadAdminTabContent();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// Admin Buses Tab
async function loadAdminBusesTab(container) {
  try {
    const buses = await apiCall("/buses");
    const routes = await apiCall("/routes");
    const drivers = await apiCall("/users?role=DRIVER");

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title">🚌 College Bus Fleet (${buses.length} Buses)</div>
          <button class="btn btn-primary" onclick="openCreateBusModal()">+ Register New Bus</button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Bus Number</th>
                <th>Registration</th>
                <th>Capacity</th>
                <th>Status</th>
                <th>Assigned Route</th>
                <th>Driver</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${buses.map(b => `
                <tr>
                  <td><strong>${escapeHtml(b.bus_number)}</strong></td>
                  <td>${escapeHtml(b.registration_number)}</td>
                  <td>${b.capacity} Seats</td>
                  <td>
                    <span class="role-tag" style="background:${b.status === 'ON_TRIP' ? 'var(--success)' : (b.status === 'IDLE' ? 'var(--primary)' : 'var(--neutral-500)')}">
                      ${b.status}
                    </span>
                  </td>
                  <td>${b.default_route ? escapeHtml(b.default_route.route_name) : "—"}</td>
                  <td>${b.current_driver ? escapeHtml(b.current_driver.full_name) : "—"}</td>
                  <td>
                    <button class="btn btn-outline" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="promptUpdateBus(${b.id}, '${b.status}')">Update Status</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
  }
}

async function promptUpdateBus(busId, currentStatus) {
  const newStatus = prompt("Enter new status (IDLE, ON_TRIP, MAINTENANCE, INACTIVE):", currentStatus);
  if (!newStatus) return;
  try {
    await apiCall(`/buses/${busId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus.toUpperCase() })
    });
    loadAdminTabContent();
  } catch (err) {
    alert("Error updating bus: " + err.message);
  }
}

// Admin Routes Tab
async function loadAdminRoutesTab(container) {
  try {
    const routes = await apiCall("/routes");
    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title">🗺️ College Transit Routes & Stops</div>
          <button class="btn btn-primary" onclick="openCreateRouteModal()">+ Add New Route</button>
        </div>
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          ${routes.map(r => `
            <div style="border: 1px solid var(--neutral-200); border-radius: var(--radius-sm); padding: 1rem; background: var(--neutral-50);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div>
                  <strong style="font-size: 1.05rem; color: var(--neutral-900);">${escapeHtml(r.route_name)}</strong>
                  <span class="role-tag" style="margin-left: 0.5rem;">${r.route_code}</span>
                </div>
                <button class="btn btn-outline" style="padding: 0.25rem 0.6rem; font-size: 0.8rem;" onclick="openAddStopModal(${r.id})">+ Add Stop</button>
              </div>
              <p style="font-size: 0.85rem; color: var(--neutral-600); margin-bottom: 0.75rem;">${escapeHtml(r.description || '')}</p>
              
              <div style="background: white; border: 1px solid var(--neutral-200); border-radius: 6px; padding: 0.5rem 0.75rem;">
                <div style="font-size: 0.8rem; font-weight: 700; color: var(--neutral-500); margin-bottom: 0.4rem; text-transform: uppercase;">
                  Fixed Infrastructure Stop Sequence:
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
                  ${r.stops.map((s, idx) => `
                    <div style="display: flex; align-items: center; gap: 0.35rem; background: var(--neutral-100); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.85rem;">
                      <span style="font-weight: 700; color: var(--primary);">${s.sequence}.</span>
                      <span>${escapeHtml(s.stop_name)}</span>
                      <small style="color: var(--neutral-500);">(${s.scheduled_offset_minutes}m)</small>
                    </div>
                    ${idx < r.stops.length - 1 ? '<span style="color: var(--neutral-400);">➔</span>' : ''}
                  `).join('')}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
  }
}

// Admin Allocations Tab
async function loadAdminAssignmentsTab(container) {
  try {
    const defaultAssigns = await apiCall("/assignments/default");
    const specialAssigns = await apiCall("/assignments/special");
    const buses = await apiCall("/buses");
    const students = await apiCall("/users?role=STUDENT");
    const staff = await apiCall("/users?role=STAFF");

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title">📋 Student & Staff Bus Allocations</div>
          <button class="btn btn-primary" onclick="openAssignModal()">+ Assign Passenger</button>
        </div>
        <p style="font-size: 0.85rem; color: var(--neutral-600); margin-bottom: 1rem;">
          Assign students and faculty to fixed infrastructure bus stops and buses. Live GPS of passengers is strictly never collected.
        </p>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Passenger</th>
                <th>Role</th>
                <th>Assigned Bus</th>
                <th>Pickup / Drop Stop</th>
                <th>Route</th>
                <th>Academic Year</th>
              </tr>
            </thead>
            <tbody>
              ${defaultAssigns.map(a => `
                <tr>
                  <td><strong>${escapeHtml(a.user ? a.user.full_name : '—')}</strong> (@${escapeHtml(a.user ? a.user.username : '')})</td>
                  <td><span class="role-tag">${a.user ? a.user.role : 'STUDENT'}</span></td>
                  <td>${escapeHtml(a.bus ? a.bus.bus_number : '—')}</td>
                  <td>${escapeHtml(a.stop ? a.stop.stop_name : '—')}</td>
                  <td>${escapeHtml(a.stop && a.stop.route_id ? `Route #${a.stop.route_id}` : '—')}</td>
                  <td>${escapeHtml(a.academic_year)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">📝 Special & Exam-Day Overrides (${specialAssigns.length})</div>
          <button class="btn btn-outline" onclick="openSpecialAssignModal()">+ Add Exam-Day Override</button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Passenger</th>
                <th>Date</th>
                <th>Assigned Bus</th>
                <th>Stop</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              ${specialAssigns.map(s => `
                <tr>
                  <td><strong>${escapeHtml(s.user ? s.user.full_name : '—')}</strong></td>
                  <td>${s.effective_date}</td>
                  <td>${escapeHtml(s.bus ? s.bus.bus_number : '—')}</td>
                  <td>${escapeHtml(s.stop ? s.stop.stop_name : '—')}</td>
                  <td><span class="badge-cost" style="background:#fef3c7; color:#b45309; border-color:#fde68a;">${escapeHtml(s.reason)}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
  }
}

// Admin Reports Tab
async function loadAdminReportsTab(container) {
  try {
    const metrics = await apiCall("/reports/eta-model-metrics");
    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title">📈 Machine Learning ETA Model Evaluation</div>
          <span class="role-tag" style="background:var(--success)">Trained & Evaluated</span>
        </div>
        
        <p style="font-size: 0.85rem; color: var(--neutral-600); margin-bottom: 1.25rem;">
          The system uses a Scikit-Learn Gradient Boosting Regressor trained with 11 engineered traffic and cyclic time features. Evaluated against the historical project baseline.
        </p>

        <div class="grid-3" style="margin-bottom: 1.5rem;">
          <div style="background: var(--neutral-100); padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.75rem; font-weight: 700; color: var(--neutral-500); text-transform: uppercase;">MAE (Mean Absolute Error)</div>
            <div style="font-size: 2rem; font-weight: 800; color: var(--primary);">${metrics.evaluation.mae} min</div>
            <small style="color: var(--neutral-600);">Baseline: <strong>${metrics.historical_baseline.mae}</strong> (${metrics.comparison.mae_status})</small>
          </div>
          <div style="background: var(--neutral-100); padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.75rem; font-weight: 700; color: var(--neutral-500); text-transform: uppercase;">RMSE (Root Mean Squared Error)</div>
            <div style="font-size: 2rem; font-weight: 800; color: var(--primary);">${metrics.evaluation.rmse} min</div>
            <small style="color: var(--neutral-600);">Baseline: <strong>${metrics.historical_baseline.rmse}</strong> (${metrics.comparison.rmse_status})</small>
          </div>
          <div style="background: var(--neutral-100); padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.75rem; font-weight: 700; color: var(--neutral-500); text-transform: uppercase;">R² Explanatory Power</div>
            <div style="font-size: 2rem; font-weight: 800; color: var(--success);">${metrics.evaluation.r2}</div>
            <small style="color: var(--neutral-600);">Baseline: <strong>${metrics.historical_baseline.r2}</strong> (${metrics.comparison.r2_status})</small>
          </div>
        </div>

        <div style="background: var(--neutral-50); border: 1px solid var(--neutral-200); border-radius: 8px; padding: 1rem;">
          <h4 style="font-size: 0.95rem; margin-bottom: 0.5rem;">Engineered ML Features:</h4>
          <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">
            ${metrics.features.map(f => `<span class="badge-cost" style="background:white; color:var(--neutral-700); border-color:var(--neutral-300);">${f}</span>`).join('')}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
  }
}

// -------------------------------------------------------------
// 3. DRIVER VIEW
// -------------------------------------------------------------
async function renderDriverView(container) {
  try {
    const activeTrip = await apiCall("/trips/driver/active");
    state.activeTrip = activeTrip;

    container.innerHTML = `
      <div style="max-width: 850px; margin: 0 auto;">
        ${!activeTrip ? `
          <div class="card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🚍</div>
            <h2>No Scheduled Trip Found</h2>
            <p style="color: var(--neutral-500); margin-top: 0.5rem;">You do not have an active or assigned trip at this moment. Contact fleet dispatch.</p>
          </div>
        ` : `
          <div class="card">
            <div class="card-header">
              <div>
                <div class="card-title">🚍 Driver Operational Console</div>
                <small style="color: var(--neutral-500);">${escapeHtml(activeTrip.trip_name)}</small>
              </div>
              <span class="role-tag" style="background: ${activeTrip.status === 'ACTIVE' ? 'var(--success)' : 'var(--neutral-500)'}; font-size: 0.85rem; padding: 0.25rem 0.75rem;">
                ${activeTrip.status}
              </span>
            </div>

            <!-- GPS Scoping Banner -->
            <div class="gps-status-indicator ${activeTrip.status === 'ACTIVE' ? 'gps-on' : 'gps-off'}" style="margin-bottom: 1.25rem;">
              <span class="${activeTrip.status === 'ACTIVE' ? 'pulse-dot' : ''}"></span>
              <span>
                ${activeTrip.status === 'ACTIVE' ? 'GPS TRANSMISSION: ACTIVE (Trip-Scoped Telemetry Broadcasting)' : 'GPS TRANSMISSION: OFF (GPS Tracking Disabled until trip starts)'}
              </span>
            </div>

            <div class="grid-3" style="margin-bottom: 1.5rem;">
              <div style="background: var(--neutral-100); padding: 0.75rem; border-radius: 6px;">
                <label>Assigned Bus</label>
                <strong>${escapeHtml(activeTrip.bus ? activeTrip.bus.bus_number : '—')}</strong>
                <div style="font-size: 0.8rem; color: var(--neutral-500);">${escapeHtml(activeTrip.bus ? activeTrip.bus.registration_number : '')}</div>
              </div>
              <div style="background: var(--neutral-100); padding: 0.75rem; border-radius: 6px;">
                <label>Route</label>
                <strong>${escapeHtml(activeTrip.route ? activeTrip.route.route_name : '—')}</strong>
              </div>
              <div style="background: var(--neutral-100); padding: 0.75rem; border-radius: 6px;">
                <label>Current Speed</label>
                <strong>${activeTrip.current_speed_kmh || 0} km/h</strong>
              </div>
            </div>

            <!-- Driver Actions -->
            <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
              ${activeTrip.status === 'NOT_STARTED' ? `
                <button class="btn btn-success btn-lg" style="flex: 1;" onclick="startDriverTrip(${activeTrip.id})">
                  ▶️ START TRIP (Enable GPS)
                </button>
              ` : (activeTrip.status === 'ACTIVE' ? `
                <button class="btn btn-danger btn-lg" style="flex: 1;" onclick="stopDriverTrip(${activeTrip.id})">
                  ⏹️ STOP TRIP (Shut Down GPS)
                </button>
              ` : `
                <button class="btn btn-outline btn-lg" style="flex: 1;" disabled>Trip ${activeTrip.status}</button>
              `)}
            </div>

            <!-- Built-in GPS Simulator & Device GPS Toggle -->
            ${activeTrip.status === 'ACTIVE' ? `
              <div style="background: #f8fafc; border: 1px solid var(--neutral-200); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                  <strong style="font-size: 0.9rem;">🛰️ GPS Transmission Simulator:</strong>
                  <button id="sim-btn" class="btn btn-primary" style="padding: 0.3rem 0.8rem; font-size: 0.85rem;" onclick="toggleGpsSimulation(${activeTrip.id})">
                    ▶️ Start Bus Route Simulator
                  </button>
                </div>
                <p style="font-size: 0.78rem; color: var(--neutral-500);">
                  Simulates realistic bus movement across sequential route stops with speed variations. Clearly identified as simulated GPS as per project requirements.
                </p>
              </div>
            ` : ''}

            <!-- Live Driver Route Map -->
            <div id="driver-map" class="map-box"></div>
          </div>
        `}
      </div>
    `;

    if (activeTrip) {
      initDriverMap(activeTrip);
    }
  } catch (err) {
    container.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
  }
}

async function startDriverTrip(tripId) {
  try {
    const updated = await apiCall(`/trips/${tripId}/start`, { method: "POST" });
    state.activeTrip = updated;
    renderApp();
  } catch (err) {
    alert("Error starting trip: " + err.message);
  }
}

async function stopDriverTrip(tripId) {
  if (!confirm("Are you sure you want to stop this trip? GPS tracking will immediately terminate.")) return;
  try {
    if (state.gpsSimInterval) {
      clearInterval(state.gpsSimInterval);
      state.gpsSimInterval = null;
    }
    const updated = await apiCall(`/trips/${tripId}/stop`, { method: "POST" });
    state.activeTrip = updated;
    renderApp();
  } catch (err) {
    alert("Error stopping trip: " + err.message);
  }
}

function toggleGpsSimulation(tripId) {
  const btn = document.getElementById("sim-btn");
  if (state.gpsSimInterval) {
    clearInterval(state.gpsSimInterval);
    state.gpsSimInterval = null;
    btn.textContent = "▶️ Start Bus Route Simulator";
    btn.className = "btn btn-primary";
    return;
  }

  btn.textContent = "⏸️ Pause Simulator";
  btn.className = "btn btn-danger";

  // Simulate pings every 3 seconds moving along the route stops
  state.gpsSimInterval = setInterval(async () => {
    try {
      const live = await apiCall(`/tracking/trip/${tripId}/live`);
      const stops = live.stops_eta;
      if (!stops || stops.length === 0) return;

      if (state.simulatedStepIdx >= stops.length) {
        state.simulatedStepIdx = 0; // Loop or reset
      }

      const targetStop = stops[state.simulatedStepIdx];
      // Add slight jitter for realism
      const lat = targetStop.latitude + (Math.random() - 0.5) * 0.001;
      const lon = targetStop.longitude + (Math.random() - 0.5) * 0.001;
      const speed = Math.floor(25 + Math.random() * 20);

      await apiCall("/tracking/ping", {
        method: "POST",
        body: JSON.stringify({
          trip_id: tripId,
          latitude: lat,
          longitude: lon,
          speed_kmh: speed,
          heading: 45.0,
          accuracy_meters: 5.0,
          is_simulated: true
        })
      });

      state.simulatedStepIdx++;
      updateDriverMapBus(lat, lon, speed);
    } catch (err) {
      console.error("Simulation error:", err);
    }
  }, 3000);
}

// -------------------------------------------------------------
// 4. STUDENT & STAFF PASSENGER VIEW
// -------------------------------------------------------------
async function renderPassengerView(container) {
  container.innerHTML = `
    <div style="max-width: 950px; margin: 0 auto;">
      <!-- Privacy Badge -->
      <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 0.5rem; color: #166534; font-size: 0.85rem; font-weight: 600;">
          <span>🛡️</span>
          <span>Privacy Guarantee: We Track The Bus, Not The Student. Your GPS is never collected or requested.</span>
        </div>
        <button class="notification-bell-btn" onclick="openNotificationDrawer()">
          🔔 <span id="notif-count-badge" class="notification-count" style="display:none">0</span>
        </button>
      </div>

      <div id="passenger-bus-container">
        <div class="card" style="text-align: center; padding: 2.5rem;">
          <p>Loading allocated bus and live ETA information...</p>
        </div>
      </div>
    </div>
  `;

  loadPassengerLiveTracking();
  fetchNotifications();
  // Poll live tracking every 4 seconds
  if (state.refreshInterval) clearInterval(state.refreshInterval);
  state.refreshInterval = setInterval(() => {
    loadPassengerLiveTracking(true);
    fetchNotifications();
  }, 4000);
}

// ── Passenger Location State ─────────────────────────────────────────────────
const passengerLocationState = {
  sessionId:       null,
  watchId:         null,       // navigator.geolocation watch handle
  tripId:          null,
  busNumber:       null,
  sharing:         false,
  pingIntervalMs:  30000,      // Send ping every 30 seconds (battery-friendly)
  lastPingSent:    0,
};

async function loadPassengerLiveTracking(isSilent = false) {
  const container = document.getElementById("passenger-bus-container");
  if (!container) return;

  try {
    const live = await apiCall("/tracking/my-bus");
    const myAssignment = await apiCall("/assignments/my-assignment");

    if (!live || !live.trip) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 2.5rem;">
          <div style="font-size: 3rem; margin-bottom: 1rem;">🚍</div>
          <h3>Bus is Not Currently on an Active Trip</h3>
          <p style="color: var(--neutral-500); margin-top: 0.5rem;">
            Your assigned bus <strong>${myAssignment.bus ? myAssignment.bus.bus_number : 'College Bus'}</strong> is currently idle.
            Tracking and live ETA will appear as soon as the driver starts the trip.
          </p>
          ${myAssignment.stop ? `
            <div style="margin-top: 1rem; background: var(--neutral-100); padding: 0.75rem; border-radius: 6px; display: inline-block;">
              Your Designated Stop: <strong>${escapeHtml(myAssignment.stop.stop_name)}</strong>
            </div>
          ` : ''}
        </div>
      `;
      return;
    }

    const trip = live.trip;
    const stopsEta = live.stops_eta || [];
    const locSource  = live.location_source     || "UNKNOWN";
    const locConf    = live.location_confidence || "UNKNOWN";
    const locLabel   = live.location_label      || "Unavailable";
    const contribCnt = live.contributor_count   || 0;

    // Find passenger's stop
    let targetStopEta = null;
    if (myAssignment.stop) {
      targetStopEta = stopsEta.find(s => s.stop_id === myAssignment.stop.id);
    }
    if (!targetStopEta && stopsEta.length > 0) {
      targetStopEta = stopsEta[0];
    }

    const etaMin   = targetStopEta ? targetStopEta.final_eta_minutes : 0;
    const isArrived = targetStopEta && targetStopEta.status === "ARRIVED";

    // Build location source badge
    const badgeClass = locSource === "DRIVER_GPS" ? "live"
                      : (locSource === "PASSENGER_ASSISTED" || locSource === "COMBINED") ? "passenger"
                      : locSource === "SCHEDULE_ESTIMATE" ? "estimated"
                      : "unavailable";
    const locationBadgeHtml = `
      <div style="margin-top:0.5rem;">
        <span class="location-badge ${badgeClass}">
          <span class="badge-dot"></span>
          ${locLabel}
        </span>
        ${contribCnt > 0 ? `<div class="contributor-row">${contribCnt} passenger${contribCnt > 1 ? 's' : ''} helping improve live location</div>` : ''}
      </div>
    `;

    // Build passenger panel (shown below the timeline)
    const isActiveTripForPassenger = trip.status === "ACTIVE";
    const sharingActive = passengerLocationState.sharing &&
                          passengerLocationState.tripId === trip.id;

    const passengerPanelHtml = isActiveTripForPassenger ? `
      ${sharingActive ? `
        <div class="sharing-active-panel" id="sharing-active-panel">
          <h4>You Are Helping Locate This Bus</h4>
          <div class="sharing-status">
            <span class="sharing-dot"></span>
            Location sharing is active for this bus trip &mdash;
            Helping locate: <strong>${escapeHtml(trip.bus ? trip.bus.bus_number : 'Bus')}</strong>
          </div>
          <button class="btn-stop-sharing" onclick="stopPassengerSharing()">Stop Sharing</button>
        </div>
      ` : `
        <div class="passenger-panel" id="passenger-panel">
          <h4>Help Improve Live Location</h4>
          <p>Are you currently travelling on this bus? Voluntarily share your location to help improve the live bus position estimate for all passengers.</p>
          <button class="btn-im-on-bus" onclick="showConsentModal(${trip.id}, '${escapeHtml(trip.bus ? trip.bus.bus_number : 'Bus')}', '${escapeHtml(trip.route ? trip.route.route_name : 'Route')}')">
            I'm On This Bus
          </button>
        </div>
      `}
    ` : '';

    if (!isSilent || !document.getElementById("passenger-map")) {
      container.innerHTML = `
        <!-- Live ETA Hero Banner -->
        <div class="eta-hero">
          <div>
            <div class="eta-tag">
              ${isArrived ? '🎉 BUS AT YOUR STOP' : 'LIVE ESTIMATED TIME OF ARRIVAL'}
            </div>
            <div class="eta-time-val">
              ${isArrived ? 'ARRIVED' : `${etaMin} <span style="font-size: 1.5rem; font-weight: 500;">MINUTES</span>`}
            </div>
            <div style="font-size: 0.95rem; opacity: 0.9; margin-top: 0.35rem;">
              Target Stop: <strong>${targetStopEta ? escapeHtml(targetStopEta.stop_name) : 'Your Stop'}</strong>
              ${targetStopEta && targetStopEta.scheduled_arrival_time ? ` (Scheduled: ${targetStopEta.scheduled_arrival_time})` : ''}
            </div>
            ${locationBadgeHtml}
          </div>
          <div style="text-align: right;">
            <span class="role-tag" style="background: rgba(255,255,255,0.25); font-size: 0.9rem; padding: 0.3rem 0.75rem;">
              ${escapeHtml(trip.bus ? trip.bus.bus_number : 'BUS')}
            </span>
            <div style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.9;">
              Speed: <strong>${trip.current_speed_kmh || 0} km/h</strong>
            </div>
            <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.25rem;">
              ETA Engine: <strong>ML Regressor</strong>
            </div>
          </div>
        </div>

        <!-- Live Map Card -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">🗺️ Live Bus Position on Route</div>
            <span class="badge-cost">Attribution: © OpenStreetMap</span>
          </div>
          <div id="passenger-map" class="map-box"></div>
        </div>

        <!-- Route Stop Progression Timeline -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">📍 Route Stop Progression &amp; Individual ETAs</div>
          </div>
          <div class="timeline">
            ${stopsEta.map(s => {
              const isTarget = targetStopEta && s.stop_id === targetStopEta.stop_id;
              let stepClass = s.status.toLowerCase();
              if (isTarget) stepClass += " target";

              return `
                <div class="timeline-step ${stepClass}">
                  <div class="timeline-dot"></div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <strong>${s.sequence}. ${escapeHtml(s.stop_name)}</strong>
                      ${isTarget ? '<span class="role-tag" style="background:var(--success); margin-left:0.5rem;">Your Stop</span>' : ''}
                      <div style="font-size: 0.8rem; color: var(--neutral-500);">
                        Scheduled: ${s.scheduled_arrival_time || '—'} | Remaining: ${s.distance_remaining_km} km
                      </div>
                    </div>
                    <div style="text-align: right;">
                      <span class="role-tag" style="background:${s.status === 'PASSED' ? 'var(--neutral-400)' : (s.status === 'ARRIVED' ? 'var(--success)' : 'var(--primary)')}">
                        ${s.status === 'ARRIVED' ? 'AT STOP' : (s.status === 'PASSED' ? 'PASSED' : `${s.final_eta_minutes} min`)}
                      </span>
                    </div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <!-- I'm On This Bus Panel -->
        ${passengerPanelHtml}
      `;

      initPassengerMap(trip, stopsEta, targetStopEta);
    } else {
      // Smooth update: refresh map marker and ETA values
      const effectiveLat = live.effective_latitude  || trip.current_latitude;
      const effectiveLon = live.effective_longitude || trip.current_longitude;
      updatePassengerMapBus(effectiveLat, effectiveLon, trip.current_speed_kmh);
    }
  } catch (err) {
    console.error("Passenger tracking error:", err);
  }
}

// ── Consent Modal ─────────────────────────────────────────────────────────────

function showConsentModal(tripId, busNumber, routeName) {
  // Remove any existing modal
  const existing = document.getElementById("consent-overlay");
  if (existing) existing.remove();

  const overlay = document.createElement("div");
  overlay.id = "consent-overlay";
  overlay.className = "consent-overlay";
  overlay.innerHTML = `
    <div class="consent-modal">
      <div class="consent-icon">📍</div>
      <h3>Are you on Bus ${escapeHtml(busNumber)}?</h3>
      <p>
        Your location will be <strong>temporarily</strong> used to help estimate
        this bus's position while you are travelling on it.<br><br>
        Route: <strong>${escapeHtml(routeName)}</strong><br><br>
        Location sharing stops automatically when the trip ends or you press Stop Sharing.
        Your identity is never exposed to other passengers.
      </p>
      <div class="consent-actions">
        <button class="btn-consent-allow" onclick="startPassengerSharing(${tripId}, '${escapeHtml(busNumber)}')">
          Allow Location &amp; Join Bus
        </button>
        <button class="btn-consent-cancel" onclick="document.getElementById('consent-overlay').remove()">
          Cancel
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
}

// ── Start Passenger Location Sharing ─────────────────────────────────────────

async function startPassengerSharing(tripId, busNumber) {
  // Close modal
  const overlay = document.getElementById("consent-overlay");
  if (overlay) overlay.remove();

  try {
    // 1. Create session (sends consent=true)
    const sessionData = await apiCall("/passenger-location/start-session", {
      method: "POST",
      body: JSON.stringify({ consent: true })
    });

    passengerLocationState.sessionId = sessionData.id;
    passengerLocationState.tripId    = tripId;
    passengerLocationState.busNumber = busNumber;
    passengerLocationState.sharing   = true;

    // 2. Request geolocation ONLY now — after explicit consent
    if (!navigator.geolocation) {
      alert("Your browser does not support GPS location. Passenger-assisted location unavailable.");
      await stopPassengerSharing();
      return;
    }

    // Use watchPosition with 30-second minimum interval (battery-friendly)
    passengerLocationState.watchId = navigator.geolocation.watchPosition(
      (position) => {
        const now = Date.now();
        if (now - passengerLocationState.lastPingSent >= passengerLocationState.pingIntervalMs) {
          passengerLocationState.lastPingSent = now;
          sendPassengerPing(position);
        }
      },
      (err) => {
        console.warn("Geolocation error:", err.message);
      },
      {
        enableHighAccuracy: true,
        timeout:            15000,
        maximumAge:         20000
      }
    );

    // Refresh the passenger panel to show "active sharing" UI
    loadPassengerLiveTracking(false);

  } catch (err) {
    console.error("Failed to start passenger sharing:", err);
    alert("Could not start location sharing: " + (err.message || "Unknown error"));
  }
}

// ── Send a Single GPS Ping ────────────────────────────────────────────────────

async function sendPassengerPing(position) {
  if (!passengerLocationState.sessionId || !passengerLocationState.sharing) return;

  const { latitude, longitude, accuracy, speed, heading } = position.coords;

  try {
    await apiCall("/passenger-location/ping", {
      method: "POST",
      body: JSON.stringify({
        session_id:      passengerLocationState.sessionId,
        latitude:        latitude,
        longitude:       longitude,
        accuracy_meters: accuracy,
        speed_kmh:       speed != null ? speed * 3.6 : null,  // m/s → km/h
        heading:         heading,
      })
    });
  } catch (err) {
    // If session expired or trip ended, stop sharing
    if (err.message && (err.message.includes("expired") || err.message.includes("active"))) {
      stopPassengerSharing();
    }
    console.warn("Ping failed:", err.message);
  }
}

// ── Stop Passenger Location Sharing ──────────────────────────────────────────

async function stopPassengerSharing() {
  // Stop the browser geolocation watch
  if (passengerLocationState.watchId !== null) {
    navigator.geolocation.clearWatch(passengerLocationState.watchId);
    passengerLocationState.watchId = null;
  }

  // Tell the server to end the session
  if (passengerLocationState.sharing) {
    try {
      await apiCall("/passenger-location/stop-session", { method: "DELETE" });
    } catch (e) {
      // Best effort — session may already be expired
    }
  }

  // Reset state
  passengerLocationState.sessionId  = null;
  passengerLocationState.tripId     = null;
  passengerLocationState.busNumber  = null;
  passengerLocationState.sharing    = false;
  passengerLocationState.lastPingSent = 0;

  // Refresh view
  loadPassengerLiveTracking(false);
}

// Clean up on page unload (logout, tab close, etc.)
window.addEventListener("beforeunload", () => {
  if (passengerLocationState.sharing) {
    if (passengerLocationState.watchId !== null) {
      navigator.geolocation.clearWatch(passengerLocationState.watchId);
    }
    // Fire-and-forget beacon to stop server session
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/passenger-location/stop-session");
    }
  }
});


// -------------------------------------------------------------
// 5. NOTIFICATIONS
// -------------------------------------------------------------
async function fetchNotifications() {
  try {
    const notifs = await apiCall("/notifications?unread_only=false&limit=15");
    state.notifications = notifs;
    const unreadCount = notifs.filter(n => !n.is_read).length;
    const badge = document.getElementById("notif-count-badge");
    if (badge) {
      if (unreadCount > 0) {
        badge.style.display = "inline-block";
        badge.textContent = unreadCount;
      } else {
        badge.style.display = "none";
      }
    }
  } catch (err) {
    // Silent
  }
}

function openNotificationDrawer() {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.id = "notif-modal";
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

  modal.innerHTML = `
    <div class="modal-content" style="max-width: 500px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
        <h3 style="font-size: 1.15rem;">🔔 Bus Arrival Notifications</h3>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="markAllNotificationsRead()">Mark All Read</button>
          <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('notif-modal').remove()">✕</button>
        </div>
      </div>

      <div style="max-height: 400px; overflow-y: auto;">
        ${state.notifications.length === 0 ? `
          <p style="text-align: center; color: var(--neutral-500); padding: 1.5rem;">No notifications yet.</p>
        ` : state.notifications.map(n => `
          <div class="notif-item ${!n.is_read ? 'unread' : ''} ${n.threshold_type === '2_MIN' || n.threshold_type === 'ARRIVED' ? 'urgent' : ''}">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
              <strong>${escapeHtml(n.title)}</strong>
              <span class="role-tag" style="background: var(--neutral-600); font-size: 0.65rem;">${n.threshold_type}</span>
            </div>
            <p style="color: var(--neutral-700);">${escapeHtml(n.message)}</p>
            <small style="color: var(--neutral-400); font-size: 0.75rem;">${new Date(n.created_at).toLocaleTimeString()}</small>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

async function markAllNotificationsRead() {
  try {
    await apiCall("/notifications/read-all", { method: "POST" });
    fetchNotifications();
    const modal = document.getElementById("notif-modal");
    if (modal) modal.remove();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// -------------------------------------------------------------
// 6. MAP ENGINE (Leaflet.js + OpenStreetMap - Free Tier ₹0)
// -------------------------------------------------------------
function initFleetMap() {
  const container = document.getElementById("fleet-map");
  if (!container || typeof L === "undefined") return;

  const map = L.map("fleet-map").setView([9.18, 77.86], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  // Fetch active fleet
  apiCall("/tracking/fleet/live").then(fleet => {
    fleet.forEach(b => {
      if (b.latitude && b.longitude) {
        const marker = L.marker([b.latitude, b.longitude]).addTo(map);
        marker.bindPopup(`
          <strong>${escapeHtml(b.bus_number)}</strong> (${escapeHtml(b.registration_number)})<br>
          Route: ${escapeHtml(b.route_name)}<br>
          Driver: ${escapeHtml(b.driver_name)}<br>
          Speed: ${b.speed_kmh} km/h
        `);
      }
    });
  });
}

function initDriverMap(trip) {
  const container = document.getElementById("driver-map");
  if (!container || typeof L === "undefined") return;

  apiCall(`/routes/${trip.route_id}`).then(route => {
    const stops = route.stops || [];
    if (stops.length === 0) return;

    const startLat = stops[0].latitude;
    const startLon = stops[0].longitude;

    const map = L.map("driver-map").setView([startLat, startLon], 13);
    state.map = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Add Stop markers & route line
    const coords = [];
    stops.forEach(s => {
      coords.push([s.latitude, s.longitude]);
      L.circleMarker([s.latitude, s.longitude], {
        radius: 7,
        fillColor: "#3b82f6",
        color: "#1e3a8a",
        weight: 2,
        fillOpacity: 0.9
      }).addTo(map).bindPopup(`<strong>Stop ${s.sequence}: ${escapeHtml(s.stop_name)}</strong>`);
    });

    state.routePolyline = L.polyline(coords, { color: "#1e40af", weight: 4, dashArray: "5, 5" }).addTo(map);
    map.fitBounds(state.routePolyline.getBounds(), { padding: [30, 30] });

    // Initial Bus Marker
    const busLat = trip.current_latitude || startLat;
    const busLon = trip.current_longitude || startLon;
    state.busMarker = L.marker([busLat, busLon]).addTo(map).bindPopup(`<strong>${trip.bus ? trip.bus.bus_number : 'Bus'}</strong>`);
  });
}

function updateDriverMapBus(lat, lon, speed) {
  if (state.busMarker && lat && lon) {
    state.busMarker.setLatLng([lat, lon]);
    state.busMarker.setPopupContent(`<strong>Bus Speed: ${speed} km/h</strong>`);
  }
}

function initPassengerMap(trip, stops, targetStop) {
  const container = document.getElementById("passenger-map");
  if (!container || typeof L === "undefined") return;

  if (stops.length === 0) return;

  const map = L.map("passenger-map").setView([stops[0].latitude, stops[0].longitude], 13);
  state.map = map;

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  const coords = [];
  stops.forEach(s => {
    coords.push([s.latitude, s.longitude]);
    const isTarget = targetStop && s.stop_id === targetStop.stop_id;

    // Highlight target stop with green ring
    L.circleMarker([s.latitude, s.longitude], {
      radius: isTarget ? 10 : 6,
      fillColor: isTarget ? "#16a34a" : "#3b82f6",
      color: isTarget ? "#14532d" : "#1e3a8a",
      weight: isTarget ? 3 : 2,
      fillOpacity: 0.9
    }).addTo(map).bindPopup(`
      <strong>${s.sequence}. ${escapeHtml(s.stop_name)}</strong>
      ${isTarget ? '<br><span style="color:#16a34a; font-weight:700;">★ Your Designated Stop</span>' : ''}
    `);
  });

  state.routePolyline = L.polyline(coords, { color: "#3b82f6", weight: 4 }).addTo(map);
  map.fitBounds(state.routePolyline.getBounds(), { padding: [30, 30] });

  // Bus Marker
  const busLat = trip.current_latitude || stops[0].latitude;
  const busLon = trip.current_longitude || stops[0].longitude;

  state.busMarker = L.marker([busLat, busLon]).addTo(map).bindPopup(`
    <strong>🚍 ${escapeHtml(trip.bus ? trip.bus.bus_number : 'Bus')}</strong><br>
    Speed: ${trip.current_speed_kmh || 0} km/h
  `);
}

function updatePassengerMapBus(lat, lon, speed) {
  if (state.busMarker && lat && lon) {
    state.busMarker.setLatLng([lat, lon]);
    state.busMarker.setPopupContent(`<strong>🚍 Bus (${speed || 0} km/h)</strong>`);
  }
}

// -------------------------------------------------------------
// 7. EXCEL BULK IMPORT MODAL WORKFLOW (Section 27)
// -------------------------------------------------------------
function openExcelImportModal() {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.id = "import-modal";

  modal.innerHTML = `
    <div class="modal-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
        <h3 style="font-size: 1.2rem;">📥 Excel Bulk Data Import</h3>
        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('import-modal').remove()">✕</button>
      </div>

      <p style="font-size: 0.85rem; color: var(--neutral-600); margin-bottom: 1.25rem;">
        Upload an Excel (.xlsx) spreadsheet to bulk-register students, staff, or drivers.
        Passports/passwords will be securely hashed with PBKDF2-SHA256. 
        <strong style="color:var(--danger)">Passenger GPS/location columns are strictly forbidden and rejected.</strong>
      </p>

      <form id="import-form" onsubmit="event.preventDefault(); handleExcelPreview();">
        <div class="form-group">
          <label>Import Record Type</label>
          <select id="import-type" name="import_type">
            <option value="student">Students (Roll Number, Department, Year)</option>
            <option value="staff">Staff / Faculty (Employee ID, Department, Designation)</option>
            <option value="driver">Drivers (License Number, Experience)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Select Excel File (.xlsx)</label>
          <input type="file" id="import-file" name="file" accept=".xlsx,.xlsm" required>
        </div>

        <button type="submit" id="btn-preview-import" class="btn btn-primary" style="width: 100%;">
          🔍 Validate & Preview Spreadsheet
        </button>
      </form>

      <div id="import-preview-result" style="margin-top: 1.25rem; display: none;"></div>
    </div>
  `;

  document.body.appendChild(modal);
}

async function handleExcelPreview() {
  const fileInput = document.getElementById("import-file");
  const typeSelect = document.getElementById("import-type");
  const resultDiv = document.getElementById("import-preview-result");
  const btn = document.getElementById("btn-preview-import");

  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Please select an Excel file.");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Validating...";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("import_type", typeSelect.value);

  try {
    const res = await apiCall("/imports/preview", {
      method: "POST",
      body: formData
    });

    resultDiv.style.display = "block";
    if (!res.valid) {
      resultDiv.innerHTML = `
        <div style="background: #fee2e2; border: 1px solid #fca5a5; border-radius: 6px; padding: 1rem; color: #991b1b; font-size: 0.85rem;">
          <strong>❌ Validation Errors Detected:</strong>
          <ul style="margin-top: 0.5rem; padding-left: 1.25rem;">
            ${res.errors.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
          </ul>
        </div>
      `;
    } else {
      window._pendingImportRecords = res.raw_valid_data;
      window._pendingImportType = res.import_type;

      resultDiv.innerHTML = `
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 1rem; color: #166534; font-size: 0.85rem; margin-bottom: 1rem;">
          <strong>✓ Validation Passed:</strong> ${res.valid_count} valid records detected without errors.
        </div>

        <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">Preview (First 10 records):</h4>
        <div class="table-container" style="max-height: 200px; margin-bottom: 1rem;">
          <table>
            <thead>
              <tr>
                ${Object.keys(res.preview_records[0] || {}).map(k => `<th>${k}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${res.preview_records.map(r => `
                <tr>
                  ${Object.values(r).map(v => `<td>${escapeHtml(String(v))}</td>`).join('')}
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <button class="btn btn-success" style="width: 100%;" onclick="handleExcelConfirm()">
          ✓ Confirm & Commit ${res.valid_count} Records to Database
        </button>
      `;
    }
  } catch (err) {
    resultDiv.style.display = "block";
    resultDiv.innerHTML = `<div style="color:red">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "🔍 Validate & Preview Spreadsheet";
  }
}

async function handleExcelConfirm() {
  if (!window._pendingImportRecords || !window._pendingImportType) return;
  try {
    const res = await apiCall("/imports/confirm", {
      method: "POST",
      body: JSON.stringify({
        import_type: window._pendingImportType,
        records: window._pendingImportRecords
      })
    });
    alert(`Success: ${res.imported_count} ${res.import_type} records imported successfully!`);
    document.getElementById("import-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Commit failed: " + err.message);
  }
}

// -------------------------------------------------------------
// 8. CREATION MODALS (Users, Buses, Routes, Assignments)
// -------------------------------------------------------------
function openCreateUserModal() {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.id = "user-modal";

  modal.innerHTML = `
    <div class="modal-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
        <h3 style="font-size: 1.15rem;">+ Create New User</h3>
        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('user-modal').remove()">✕</button>
      </div>

      <form id="create-user-form" onsubmit="event.preventDefault(); submitCreateUser(this);">
        <div class="grid-2">
          <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required>
          </div>
          <div class="form-group">
            <label>Full Name</label>
            <input type="text" name="full_name" required>
          </div>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label>Email</label>
            <input type="email" name="email">
          </div>
          <div class="form-group">
            <label>Phone</label>
            <input type="text" name="phone">
          </div>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
          </div>
          <div class="form-group">
            <label>Role</label>
            <select name="role" required>
              <option value="STUDENT">Student</option>
              <option value="STAFF">Staff / Faculty</option>
              <option value="DRIVER">Driver</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;">Create User</button>
      </form>
    </div>
  `;

  document.body.appendChild(modal);
}

async function submitCreateUser(form) {
  try {
    await apiCall("/users", {
      method: "POST",
      body: JSON.stringify({
        username: form.username.value,
        full_name: form.full_name.value,
        email: form.email.value || null,
        phone: form.phone.value || null,
        password: form.password.value,
        role: form.role.value
      })
    });
    alert("User created successfully!");
    document.getElementById("user-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Error creating user: " + err.message);
  }
}

function openCreateBusModal() {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.id = "bus-modal";

  modal.innerHTML = `
    <div class="modal-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
        <h3 style="font-size: 1.15rem;">+ Register New Bus</h3>
        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('bus-modal').remove()">✕</button>
      </div>

      <form onsubmit="event.preventDefault(); submitCreateBus(this);">
        <div class="grid-2">
          <div class="form-group">
            <label>Bus Identifier (e.g. BUS-03)</label>
            <input type="text" name="bus_number" required>
          </div>
          <div class="form-group">
            <label>Registration Number (e.g. TN-67-CB-1003)</label>
            <input type="text" name="registration_number" required>
          </div>
        </div>
        <div class="form-group">
          <label>Seating Capacity</label>
          <input type="number" name="capacity" value="50" min="10" max="100" required>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Register Bus</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

async function submitCreateBus(form) {
  try {
    await apiCall("/buses", {
      method: "POST",
      body: JSON.stringify({
        bus_number: form.bus_number.value,
        registration_number: form.registration_number.value,
        capacity: parseInt(form.capacity.value),
        status: "IDLE"
      })
    });
    alert("Bus registered successfully!");
    document.getElementById("bus-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

function openCreateRouteModal() {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.id = "route-modal";

  modal.innerHTML = `
    <div class="modal-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
        <h3 style="font-size: 1.15rem;">+ Add New Route</h3>
        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('route-modal').remove()">✕</button>
      </div>

      <form onsubmit="event.preventDefault(); submitCreateRoute(this);">
        <div class="grid-2">
          <div class="form-group">
            <label>Route Name</label>
            <input type="text" name="route_name" placeholder="e.g. Route 3 - East Circle to Campus" required>
          </div>
          <div class="form-group">
            <label>Route Code</label>
            <input type="text" name="route_code" placeholder="e.g. R-03" required>
          </div>
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea name="description" rows="2"></textarea>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Create Route</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

async function submitCreateRoute(form) {
  try {
    await apiCall("/routes", {
      method: "POST",
      body: JSON.stringify({
        route_name: form.route_name.value,
        route_code: form.route_code.value,
        description: form.description.value
      })
    });
    alert("Route created successfully!");
    document.getElementById("route-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

function openAddStopModal(routeId) {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.id = "stop-modal";

  modal.innerHTML = `
    <div class="modal-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
        <h3 style="font-size: 1.15rem;">+ Add Stop to Route</h3>
        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('stop-modal').remove()">✕</button>
      </div>

      <form onsubmit="event.preventDefault(); submitCreateStop(this, ${routeId});">
        <div class="form-group">
          <label>Stop Name</label>
          <input type="text" name="stop_name" placeholder="e.g. Market Arch" required>
        </div>
        <div class="grid-3">
          <div class="form-group">
            <label>Sequence</label>
            <input type="number" name="sequence" min="1" value="1" required>
          </div>
          <div class="form-group">
            <label>Latitude (-90 to +90)</label>
            <input type="number" step="0.0001" name="latitude" value="9.18" required>
          </div>
          <div class="form-group">
            <label>Longitude (-180 to +180)</label>
            <input type="number" step="0.0001" name="longitude" value="77.86" required>
          </div>
        </div>
        <div class="form-group">
          <label>Scheduled Offset (minutes from route start)</label>
          <input type="number" name="scheduled_offset_minutes" value="15" min="0" required>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Add Stop</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

async function submitCreateStop(form, routeId) {
  try {
    await apiCall("/stops", {
      method: "POST",
      body: JSON.stringify({
        route_id: routeId,
        stop_name: form.stop_name.value,
        sequence: parseInt(form.sequence.value),
        latitude: parseFloat(form.latitude.value),
        longitude: parseFloat(form.longitude.value),
        scheduled_offset_minutes: parseInt(form.scheduled_offset_minutes.value)
      })
    });
    alert("Stop added successfully!");
    document.getElementById("stop-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function openAssignModal() {
  try {
    const users = await apiCall("/users");
    const passengers = users.filter(u => u.role === "STUDENT" || u.role === "STAFF");
    const buses = await apiCall("/buses");
    const routes = await apiCall("/routes");

    const allStops = [];
    routes.forEach(r => {
      (r.stops || []).forEach(s => allStops.push({ ...s, route_name: r.route_name }));
    });

    const modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.id = "assign-modal";

    modal.innerHTML = `
      <div class="modal-content">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
          <h3 style="font-size: 1.15rem;">+ Assign Bus & Stop to Passenger</h3>
          <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('assign-modal').remove()">✕</button>
        </div>

        <form onsubmit="event.preventDefault(); submitAssignment(this);">
          <div class="form-group">
            <label>Select Student / Faculty Member</label>
            <select name="user_id" required>
              ${passengers.map(p => `<option value="${p.id}">${escapeHtml(p.full_name)} (@${escapeHtml(p.username)} - ${p.role})</option>`).join('')}
            </select>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label>Bus</label>
              <select name="bus_id" required>
                ${buses.map(b => `<option value="${b.id}">${escapeHtml(b.bus_number)} (${escapeHtml(b.registration_number)})</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label>Stop</label>
              <select name="stop_id" required>
                ${allStops.map(s => `<option value="${s.id}">${escapeHtml(s.stop_name)} (${escapeHtml(s.route_name)})</option>`).join('')}
              </select>
            </div>
          </div>

          <button type="submit" class="btn btn-primary" style="width: 100%;">Save Allocation</button>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function submitAssignment(form) {
  try {
    await apiCall("/assignments/default", {
      method: "POST",
      body: JSON.stringify({
        user_id: parseInt(form.user_id.value),
        bus_id: parseInt(form.bus_id.value),
        stop_id: parseInt(form.stop_id.value),
        academic_year: "2025-2026"
      })
    });
    alert("Allocation saved successfully!");
    document.getElementById("assign-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function openSpecialAssignModal() {
  try {
    const users = await apiCall("/users");
    const passengers = users.filter(u => u.role === "STUDENT" || u.role === "STAFF");
    const buses = await apiCall("/buses");
    const routes = await apiCall("/routes");

    const allStops = [];
    routes.forEach(r => {
      (r.stops || []).forEach(s => allStops.push({ ...s, route_name: r.route_name }));
    });

    const modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.id = "special-modal";

    const todayStr = new Date().toISOString().split('T')[0];

    modal.innerHTML = `
      <div class="modal-content">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--neutral-200); padding-bottom: 0.5rem;">
          <h3 style="font-size: 1.15rem;">+ Add Exam-Day Special Assignment</h3>
          <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="document.getElementById('special-modal').remove()">✕</button>
        </div>

        <form onsubmit="event.preventDefault(); submitSpecialAssignment(this);">
          <div class="form-group">
            <label>Select Student / Faculty Member</label>
            <select name="user_id" required>
              ${passengers.map(p => `<option value="${p.id}">${escapeHtml(p.full_name)} (@${escapeHtml(p.username)})</option>`).join('')}
            </select>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label>Bus</label>
              <select name="bus_id" required>
                ${buses.map(b => `<option value="${b.id}">${escapeHtml(b.bus_number)}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label>Stop</label>
              <select name="stop_id" required>
                ${allStops.map(s => `<option value="${s.id}">${escapeHtml(s.stop_name)}</option>`).join('')}
              </select>
            </div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label>Effective Date</label>
              <input type="date" name="effective_date" value="${todayStr}" required>
            </div>
            <div class="form-group">
              <label>Reason / Exam Tag</label>
              <input type="text" name="reason" value="Semester Exam - Hall B" required>
            </div>
          </div>

          <button type="submit" class="btn btn-primary" style="width: 100%;">Create Override</button>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function submitSpecialAssignment(form) {
  try {
    await apiCall("/assignments/special", {
      method: "POST",
      body: JSON.stringify({
        user_id: parseInt(form.user_id.value),
        bus_id: parseInt(form.bus_id.value),
        stop_id: parseInt(form.stop_id.value),
        effective_date: form.effective_date.value,
        reason: form.reason.value
      })
    });
    alert("Exam-day override created successfully!");
    document.getElementById("special-modal").remove();
    loadAdminTabContent();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// Utility
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Global Initialization
window.addEventListener("DOMContentLoaded", () => {
  renderApp();
});
