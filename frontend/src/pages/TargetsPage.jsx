import { useState, useEffect } from "react";
import { targetsApi } from "../services/api";
import { Link } from "react-router-dom";
import { Target, Plus, CheckCircle, AlertCircle, Loader } from "lucide-react";
import StatusBadge from "../components/common/StatusBadge";

const TARGET_TYPES = [
  { value: "web_application", label: "Web Application" },
  { value: "api", label: "API" },
  { value: "host_ip", label: "Host / IP" },
  { value: "docker_image", label: "Docker Image" },
  { value: "kubernetes", label: "Kubernetes" },
  { value: "source_repository", label: "Source Repository" },
];

const ENVS = ["development", "staging", "production", "internal"];

function TargetForm({ onSuccess, onClose }) {
  const [form, setForm] = useState({
    name: "", target_type: "host_ip", address: "", environment: "development",
    owner: "", description: "", authorization_confirmed: false, authorization_note: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.authorization_confirmed) {
      setError("You must confirm authorization before adding a target.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await targetsApi.create(form);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create target");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-surface-800 border border-surface-600 rounded-lg w-full max-w-lg p-5">
        <h2 className="text-sm font-semibold text-gray-100 mb-4">Add Authorized Target</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Target Name</label>
              <input className="input" required value={form.name} onChange={(e) => set("name", e.target.value)} />
            </div>
            <div>
              <label className="label">Type</label>
              <select className="input" value={form.target_type} onChange={(e) => set("target_type", e.target.value)}>
                {TARGET_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Address (URL, IP, hostname, or image name)</label>
            <input className="input" required value={form.address} onChange={(e) => set("address", e.target.value)} placeholder="e.g. 192.168.1.10 or https://app.internal" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Environment</label>
              <select className="input" value={form.environment} onChange={(e) => set("environment", e.target.value)}>
                {ENVS.map((e) => <option key={e} value={e}>{e}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Owner</label>
              <input className="input" required value={form.owner} onChange={(e) => set("owner", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input" rows={2} value={form.description} onChange={(e) => set("description", e.target.value)} />
          </div>
          <div>
            <label className="label">Authorization Note</label>
            <input className="input" placeholder="e.g. Ticket #123, approved by security lead on 2026-08-31" value={form.authorization_note} onChange={(e) => set("authorization_note", e.target.value)} />
          </div>
          <div className="flex items-start gap-2 bg-yellow-900/20 border border-yellow-700/40 rounded p-3">
            <input
              type="checkbox"
              id="auth_confirm"
              checked={form.authorization_confirmed}
              onChange={(e) => set("authorization_confirmed", e.target.checked)}
              className="mt-0.5"
            />
            <label htmlFor="auth_confirm" className="text-xs text-yellow-300">
              I confirm that I am authorized to perform security testing against this target.
              Unauthorized testing is prohibited.
            </label>
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Adding…" : "Add Target"}
            </button>
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TargetsPage() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = () => targetsApi.list().then((r) => setTargets(r.data)).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-100">Authorized Targets</h1>
        <button className="btn-primary flex items-center gap-1.5 text-xs" onClick={() => setShowForm(true)}>
          <Plus size={13} /> Add Target
        </button>
      </div>

      {showForm && (
        <TargetForm
          onSuccess={() => { setShowForm(false); load(); }}
          onClose={() => setShowForm(false)}
        />
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader size={14} className="animate-spin" /> Loading…</div>
      ) : targets.length === 0 ? (
        <div className="card text-center text-gray-500 text-sm py-10">
          No authorized targets. Add one to start scanning.
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-surface-600">
                <th className="pb-2 pr-4">Name</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Address</th>
                <th className="pb-2 pr-4">Environment</th>
                <th className="pb-2 pr-4">Owner</th>
                <th className="pb-2 pr-4">Authorized</th>
                <th className="pb-2">Last Scanned</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((t) => (
                <tr key={t.id} className="border-b border-surface-700/50 hover:bg-surface-700/20">
                  <td className="py-2 pr-4 text-gray-200 font-medium">{t.name}</td>
                  <td className="py-2 pr-4 text-gray-400 text-xs">{t.target_type?.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4 text-gray-400 font-mono text-xs truncate max-w-[200px]">{t.address}</td>
                  <td className="py-2 pr-4 text-gray-500 text-xs capitalize">{t.environment}</td>
                  <td className="py-2 pr-4 text-gray-400 text-xs">{t.owner}</td>
                  <td className="py-2 pr-4">
                    {t.authorization_confirmed
                      ? <CheckCircle size={14} className="text-accent-green" />
                      : <AlertCircle size={14} className="text-accent-red" />}
                  </td>
                  <td className="py-2 text-gray-500 text-xs">
                    {t.last_scanned_at ? new Date(t.last_scanned_at).toLocaleDateString() : "Never"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
