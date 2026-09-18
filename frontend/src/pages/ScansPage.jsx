import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { scansApi } from "../services/api";
import { Plus, Loader } from "lucide-react";
import StatusBadge from "../components/common/StatusBadge";

export default function ScansPage() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    scansApi.list().then((r) => setScans(r.data)).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-100">Scans</h1>
        <Link to="/scans/new" className="btn-primary flex items-center gap-1.5 text-xs">
          <Plus size={13} /> New Scan
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader size={14} className="animate-spin" /> Loading…</div>
      ) : scans.length === 0 ? (
        <div className="card text-center text-gray-500 text-sm py-10">
          No scans yet. <Link to="/scans/new" className="text-accent-blue hover:underline">Start one</Link>.
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-surface-600">
                <th className="pb-2 pr-4">Scan ID</th>
                <th className="pb-2 pr-4">Profile</th>
                <th className="pb-2 pr-4">Tools</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Progress</th>
                <th className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="border-b border-surface-700/50 hover:bg-surface-700/20">
                  <td className="py-2 pr-4">
                    <Link to={`/scans/${s.id}`} className="text-accent-blue hover:underline font-mono text-xs">
                      {s.id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-gray-300 text-xs">{s.scan_profile?.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4 text-gray-400 text-xs">{s.tools?.join(", ")}</td>
                  <td className="py-2 pr-4"><StatusBadge status={s.status} /></td>
                  <td className="py-2 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-surface-600 rounded-full">
                        <div
                          className="h-1.5 bg-accent-blue rounded-full transition-all"
                          style={{ width: `${s.progress || 0}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{s.progress || 0}%</span>
                    </div>
                  </td>
                  <td className="py-2 text-gray-500 text-xs">
                    {new Date(s.created_at).toLocaleString()}
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
