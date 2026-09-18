import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { scansApi } from "../services/api";
import { Loader } from "lucide-react";
import StatusBadge from "../components/common/StatusBadge";

function SevCount({ value, cls }) {
  if (!value) return <span className="text-gray-600">—</span>;
  return <span className={`font-semibold ${cls}`}>{value}</span>;
}

export default function ScanHistoryPage() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    scansApi.history().then((r) => setScans(r.data)).finally(() => setLoading(false));
  }, []);

  const duration = (scan) => {
    if (!scan.started_at || !scan.completed_at) return "—";
    const secs = Math.round((new Date(scan.completed_at) - new Date(scan.started_at)) / 1000);
    if (secs < 60) return `${secs}s`;
    return `${Math.floor(secs / 60)}m ${secs % 60}s`;
  };

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-gray-100">Scan History</h1>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader size={14} className="animate-spin" /> Loading…</div>
      ) : scans.length === 0 ? (
        <div className="card text-center text-gray-500 text-sm py-10">No scan history yet.</div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-surface-600">
                <th className="pb-2 pr-4">Scan ID</th>
                <th className="pb-2 pr-4">Target</th>
                <th className="pb-2 pr-4">Profile</th>
                <th className="pb-2 pr-4">Date</th>
                <th className="pb-2 pr-4">Duration</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-2 text-red-400">C</th>
                <th className="pb-2 pr-2 text-orange-400">H</th>
                <th className="pb-2 pr-2 text-yellow-400">M</th>
                <th className="pb-2 pr-2 text-blue-400">L</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="border-b border-surface-700/50 hover:bg-surface-700/20">
                  <td className="py-2 pr-4">
                    <Link to={`/scans/${s.id}`} className="text-accent-blue hover:underline font-mono text-xs">
                      {s.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-gray-300 text-xs">{s.target_name}</td>
                  <td className="py-2 pr-4 text-gray-400 text-xs">{s.scan_profile?.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4 text-gray-500 text-xs">{new Date(s.created_at).toLocaleDateString()}</td>
                  <td className="py-2 pr-4 text-gray-500 text-xs">{duration(s)}</td>
                  <td className="py-2 pr-4"><StatusBadge status={s.status} /></td>
                  <td className="py-2 pr-2 text-xs"><SevCount value={s.critical_count} cls="text-red-400" /></td>
                  <td className="py-2 pr-2 text-xs"><SevCount value={s.high_count} cls="text-orange-400" /></td>
                  <td className="py-2 pr-2 text-xs"><SevCount value={s.medium_count} cls="text-yellow-400" /></td>
                  <td className="py-2 pr-2 text-xs"><SevCount value={s.low_count} cls="text-blue-400" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
