import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("vapt_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("vapt_token");
      localStorage.removeItem("vapt_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  login: (data) => api.post("/auth/login", data),
  register: (data) => api.post("/auth/register", data),
};

export const targetsApi = {
  list: () => api.get("/targets"),
  get: (id) => api.get(`/targets/${id}`),
  create: (data) => api.post("/targets", data),
  update: (id, data) => api.patch(`/targets/${id}`, data),
  deactivate: (id) => api.delete(`/targets/${id}`),
};

export const scansApi = {
  list: () => api.get("/scans"),
  get: (id) => api.get(`/scans/${id}`),
  create: (data) => api.post("/scans", data),
  cancel: (id) => api.post(`/scans/${id}/cancel`),
  history: () => api.get("/scans/history/summary"),
  compare: (scanA, scanB) => api.get("/scans/compare", { params: { scan_a: scanA, scan_b: scanB } }),
};

export const findingsApi = {
  list: (params) => api.get("/findings", { params }),
  get: (id) => api.get(`/findings/${id}`),
  update: (id, data) => api.patch(`/findings/${id}`, data),
  addNote: (id, data) => api.post(`/findings/${id}/notes`, data),
  getNotes: (id) => api.get(`/findings/${id}/notes`),
  getHistory: (id) => api.get(`/findings/${id}/history`),
};

export const dashboardApi = {
  summary: () => api.get("/dashboard/summary"),
};

export const reportsApi = {
  generate: (scanId, data) => api.post(`/scans/${scanId}/reports`, data),
  list: (scanId) => api.get(`/scans/${scanId}/reports`),
  download: (reportId) => api.get(`/reports/${reportId}/download`, { responseType: "arraybuffer" }),
};

export const retestsApi = {
  request: (findingId) => api.post(`/findings/${findingId}/retests`),
  list: (findingId) => api.get(`/findings/${findingId}/retests`),
  complete: (retestId, data) => api.patch(`/retests/${retestId}`, data),
};

export default api;
