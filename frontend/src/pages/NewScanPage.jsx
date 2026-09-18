import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { targetsApi, scansApi } from "../services/api";
import { AlertTriangle, Shield } from "lucide-react";

const PROFILES = [
  { value: "quick_scan", label: "Quick Scan", tools: ["nmap"], description: "Nmap port/service discovery" },
  { value: "web_api_scan", label: "Web / API Scan", tools: ["zap"], description: "OWASP ZAP web scanning" },
  { value: "network_scan", label: "Network Scan", tools: ["nmap"], description: "Full Nmap network analysis" },
  { value: "container_scan", label: "Container Scan", tools: ["trivy"], description: "Trivy image vulnerability scan" },
  { value: "full_vapt", label: "Full VAPT", tools: ["nmap", "zap", "trivy"], description: "All tools combined" },
];

const ALL_TOOLS = [
  { value: "nmap", label: "Nmap", desc: "Network/port discovery" },
  { value: "zap", label: "OWASP ZAP", desc: "Web application scanning" },
  { value: "trivy", label: "Trivy", desc: "Container/dependency scanning" },
  { value: "semgrep", label: "Semgrep (optional)", desc: "Source code SAST" },
];

const INTENSITIES = [
  { value: "passive", label: "Passive", desc: "Low-impact, non-intrusive" },
  { value: "normal", label: "Normal", desc: "Standard scan (recommended)" },
  { value: "aggressive", label: "Aggressive", desc: "Deep scan — use only on authorized targets" },
];

export default function NewScanPage() {
  const navigate = useNavigate();
  const [targets, setTargets] = useState([]);
  const [form, setForm] = useState({
    target_id: "",
    scan_profile: "quick_scan",
    tools: ["nmap"],
    intensity: "normal",
    scan_options: {},
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    targetsApi.list().then((r) => setTargets(r.data.filter((t) => t.authorization_confirmed)));
  }, []);

  const selectProfile = (profile) => {
    setForm((f) => ({ ...f, scan_profile: profile.value, tools: [...profile.tools] }));
  };

  const toggleTool = (tool) => {
    setForm((f) => ({
      ...f,
      tools: f.tools.includes(tool) ? f.tools.filter((t) => t !== tool) : [...f.tools, tool],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.target_id) { setError("Select an authorized target"); return; }
    if (form.tools.length === 0) { setError("Select at least one tool"); return; }
    setError("");
    setLoading(true);
    try {
      const { data } = await scansApi.create(form);
      navigate(`/scans/${data.scan_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create scan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-5">
      <h1 className="text-lg font-semibold text-gray-100">New Scan</h1>

      <div className="flex items-start gap-2 bg-yellow-900/20 border border-yellow-700/40 rounded p-3">
        <AlertTriangle size={14} className="text-yellow-400 mt-0.5 shrink-0" />
        <p className="text-xs text-yellow-300">
          Active penetration testing must only be performed against explicitly authorized targets.
          Unauthorized testing is illegal and violates platform policy.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Target selection */}
        <div className="card">
          <label className="label">Authorized Target</label>
          {targets.length === 0 ? (
            <p className="text-xs text-gray-500">No authorized targets available. Add one in <a href="/targets" className="text-accent-blue hover:underline">Targets</a>.</p>
          ) : (
            <select
              className="input"
              required
              value={form.target_id}
              onChange={(e) => setForm((f) => ({ ...f, target_id: e.target.value }))}
            >
              <option value="">— Select target —</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>{t.name} ({t.address})</option>
              ))}
            </select>
          )}
        </div>

        {/* Profile */}
        <div className="card">
          <label className="label mb-2">Scan Profile</label>
          <div className="grid grid-cols-1 gap-2">
            {PROFILES.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => selectProfile(p)}
                className={`text-left p-3 rounded border transition-colors ${
                  form.scan_profile === p.value
                    ? "border-accent-blue bg-accent-blue/10 text-accent-blue"
                    : "border-surface-600 hover:border-surface-500 text-gray-300"
                }`}
              >
                <div className="text-sm font-medium">{p.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{p.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Tools */}
        <div className="card">
          <label className="label mb-2">Tools</label>
          <div className="grid grid-cols-2 gap-2">
            {ALL_TOOLS.map((t) => (
              <label key={t.value} className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.tools.includes(t.value)}
                  onChange={() => toggleTool(t.value)}
                  className="mt-0.5"
                />
                <span>
                  <span className="text-sm text-gray-200">{t.label}</span>
                  <span className="block text-xs text-gray-500">{t.desc}</span>
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Intensity */}
        <div className="card">
          <label className="label mb-2">Scan Intensity</label>
          <div className="space-y-2">
            {INTENSITIES.map((i) => (
              <label key={i.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="intensity"
                  value={i.value}
                  checked={form.intensity === i.value}
                  onChange={() => setForm((f) => ({ ...f, intensity: i.value }))}
                />
                <span>
                  <span className="text-sm text-gray-200">{i.label}</span>
                  <span className="text-xs text-gray-500 ml-2">— {i.desc}</span>
                </span>
              </label>
            ))}
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertTriangle size={14} /> {error}
          </div>
        )}

        <div className="flex gap-2">
          <button type="submit" className="btn-primary flex items-center gap-1.5" disabled={loading}>
            <Shield size={13} /> {loading ? "Starting…" : "Start Scan"}
          </button>
          <button type="button" className="btn-secondary" onClick={() => navigate("/scans")}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
