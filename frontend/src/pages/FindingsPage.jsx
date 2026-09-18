import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { findingsApi } from "../services/api";
import { Loader } from "lucide-react";
import SeverityBadge from "../components/common/SeverityBadge";
import StatusBadge from "../components/common/StatusBadge";

const SEVERITIES = ["", "critical", "high", "medium", "low", "informational"];
const STATUSES = ["", "open", "assigned", "in_progress", "fixed", "retest_required", "closed", "false_positive"];

export default function FindingsPage() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ severity: "", status: "open" });

  const load = () => {
    const params = {};
    if (filters.severity) params.severity = filters.severity;
    if (filters.status) params.status = filters.status;
    findingsApi.list(params).then((r) => setFindings(r.data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filters]);

  const set = (k, v) => setFilters((f) => ({ ...f, [k]: v }));

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-gray-100">Findings</h1>

      <div className="flex gap-3">
        <select className="input w-auto" value={filters.severity} onChange={(e) => set("severity", e.target.value)}>
          {SEVERITIES.map((s) => <option key={s} value={s}>{s || "All Severities"}</option>)}
        </select>
        <select className="input w-auto" value={filters.status} onChange={(e) => set("status", e.target.value)}>
          {STATUSES.map((s) => <option key={s} value={s}>{s || "All Statuses"}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader size={14} className="animate-spin" /> Loading…</div>
      ) : findings.length === 0 ? (
        <div className="card text-center text-gray-500 text-sm py-10">No findings match the current filters.</div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-surface-600">
                <th className="pb-2 pr-4">Severity</th>
                <th className="pb-2 pr-4">Title</th>
                <th className="pb-2 pr-4">Tool</th>
                <th className="pb-2 pr-4">CVE</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2">Detected</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((f) => (
                <tr key={f.id} className="border-b border-surface-700/50 hover:bg-surface-700/20">
                  <td className="py-2 pr-4"><SeverityBadge severity={f.severity} /></td>
                  <td className="py-2 pr-4 max-w-xs">
                    <Link to={`/findings/${f.id}`} className="text-gray-200 hover:text-accent-blue line-clamp-2">
                      {f.title}
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-gray-400 text-xs uppercase">{f.source_tool}</td>
                  <td className="py-2 pr-4 text-gray-400 text-xs font-mono">{f.cve || "—"}</td>
                  <td className="py-2 pr-4"><StatusBadge status={f.status} /></td>
                  <td className="py-2 text-gray-500 text-xs">
                    {new Date(f.first_detected).toLocaleDateString()}
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
