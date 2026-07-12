const API_BASE_URL = 'http://127.0.0.1:8000';
const TOKEN_KEY = 'assetflow_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || `Request failed (${response.status})`;
    throw new Error(typeof message === 'string' ? message : 'Request failed');
  }
  return data;
}

// --- Auth ---------------------------------------------------------------------
export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: { email, password }, auth: false });
export const register = (full_name, email, password) =>
  request('/auth/register', { method: 'POST', body: { full_name, email, password }, auth: false });
export const fetchMe = () => request('/auth/me');
export const forgotPassword = (email) =>
  request('/auth/forgot-password', { method: 'POST', body: { email }, auth: false });
export const resetPassword = (token, new_password) =>
  request('/auth/reset-password', { method: 'POST', body: { token, new_password }, auth: false });

// --- Dashboard ----------------------------------------------------------------
export const fetchKpis = () => request('/dashboard/kpis');

// --- Organization -------------------------------------------------------------
export const fetchDepartments = () => request('/departments');
export const createDepartment = (payload) => request('/departments', { method: 'POST', body: payload });
export const updateDepartment = (id, payload) => request(`/departments/${id}`, { method: 'PATCH', body: payload });
export const deleteDepartment = (id) => request(`/departments/${id}`, { method: 'DELETE' });

export const fetchCategories = () => request('/asset-categories');
export const createCategory = (payload) => request('/asset-categories', { method: 'POST', body: payload });
export const updateCategory = (id, payload) => request(`/asset-categories/${id}`, { method: 'PATCH', body: payload });
export const deleteCategory = (id) => request(`/asset-categories/${id}`, { method: 'DELETE' });

export const fetchEmployees = () => request('/employees');
export const createEmployee = (payload) => request('/employees', { method: 'POST', body: payload });
export const updateEmployee = (id, payload) => request(`/employees/${id}`, { method: 'PATCH', body: payload });
export const deleteEmployee = (id) => request(`/employees/${id}`, { method: 'DELETE' });

// --- Assets -------------------------------------------------------------------
export const fetchAssets = (params = {}) => {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString();
  return request(`/assets${qs ? `?${qs}` : ''}`);
};
export const registerAsset = (payload) => request('/assets', { method: 'POST', body: payload });
export const updateAsset = (id, payload) => request(`/assets/${id}`, { method: 'PATCH', body: payload });
export const deleteAsset = (id) => request(`/assets/${id}`, { method: 'DELETE' });
export const fetchAssetHistory = (id) => request(`/assets/${id}/history`);
export const fetchAssetMaintenanceHistory = (id) => request(`/assets/${id}/maintenance-history`);

// --- Allocations & transfers --------------------------------------------------
export const fetchAllocations = (status) => request(`/allocations${status ? `?status=${status}` : ''}`);
export const allocateAsset = (payload) => request('/allocations', { method: 'POST', body: payload });
export const returnAllocation = (id, payload) => request(`/allocations/${id}/return`, { method: 'POST', body: payload });

export const fetchTransfers = () => request('/transfers');
export const requestTransfer = (payload) => request('/transfers', { method: 'POST', body: payload });
export const approveTransfer = (id) => request(`/transfers/${id}/approve`, { method: 'POST' });
export const rejectTransfer = (id) => request(`/transfers/${id}/reject`, { method: 'POST' });

// --- Bookings -----------------------------------------------------------------
export const fetchBookings = (resource) => request(`/bookings${resource ? `?resource=${encodeURIComponent(resource)}` : ''}`);
export const createBooking = (payload) => request('/bookings', { method: 'POST', body: payload });
export const rescheduleBooking = (id, payload) => request(`/bookings/${id}/reschedule`, { method: 'POST', body: payload });
export const cancelBooking = (id) => request(`/bookings/${id}/cancel`, { method: 'POST' });

// --- Maintenance --------------------------------------------------------------
export const fetchMaintenanceRequests = (status) =>
  request(`/maintenance-requests${status ? `?status=${encodeURIComponent(status)}` : ''}`);
export const raiseMaintenanceRequest = (payload) => request('/maintenance-requests', { method: 'POST', body: payload });
export const approveMaintenance = (id) => request(`/maintenance-requests/${id}/approve`, { method: 'POST' });
export const rejectMaintenance = (id) => request(`/maintenance-requests/${id}/reject`, { method: 'POST' });
export const assignMaintenance = (id, technician) => request(`/maintenance-requests/${id}/assign`, { method: 'POST', body: { technician } });
export const startMaintenance = (id) => request(`/maintenance-requests/${id}/start`, { method: 'POST' });
export const resolveMaintenance = (id, resolution_notes) => request(`/maintenance-requests/${id}/resolve`, { method: 'POST', body: { resolution_notes } });

// --- Asset audit --------------------------------------------------------------
export const fetchAuditCycles = () => request('/audit-cycles');
export const fetchAuditCycle = (id) => request(`/audit-cycles/${id}`);
export const createAuditCycle = (payload) => request('/audit-cycles', { method: 'POST', body: payload });
export const assignAuditors = (id, auditor_ids) => request(`/audit-cycles/${id}/auditors`, { method: 'POST', body: { auditor_ids } });
export const updateAuditItem = (id, payload) => request(`/audit-items/${id}`, { method: 'PATCH', body: payload });
export const fetchAuditDiscrepancies = (id) => request(`/audit-cycles/${id}/discrepancies`);
export const closeAuditCycle = (id) => request(`/audit-cycles/${id}/close`, { method: 'POST' });

// --- Notifications ------------------------------------------------------------
export const fetchNotifications = (unreadOnly = false) =>
  request(`/notifications${unreadOnly ? '?unread_only=true' : ''}`);
export const fetchUnreadCount = () => request('/notifications/unread-count');
export const markNotificationRead = (id) => request(`/notifications/${id}/read`, { method: 'POST' });
export const markAllNotificationsRead = () => request('/notifications/read-all', { method: 'POST' });

// --- Activity log -------------------------------------------------------------
export const fetchActivityLogs = (params = {}) => {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString();
  return request(`/activity-logs${qs ? `?${qs}` : ''}`);
};

// --- Reports & analytics ------------------------------------------------------
export const fetchReportSummary = () => request('/reports/summary');
export const fetchAssetUtilization = () => request('/reports/asset-utilization');
export const fetchMaintenanceFrequency = () => request('/reports/maintenance-frequency');
export const fetchDueMaintenance = () => request('/reports/due-maintenance');
export const fetchDepartmentAllocation = () => request('/reports/department-allocation');
export const fetchBookingHeatmap = () => request('/reports/booking-heatmap');
