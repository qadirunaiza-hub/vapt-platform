import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { scansApi, findingsApi } from "../services/api";
import { CheckCircle, XCircle, Loader, Clock, StopCircle } from "lucide-react";
import StatusBadge from "../components/common/StatusBadge";
import SeverityBadge from "../components/common/SeverityBadge";

function ToolStatus({ job }) {
  const icon = {
    completed: <CheckCircle size={14} className="text-accent-green" />,
    failed: <XCircle size={14} className="text-accent-red" />,
    running: <Loader size={14} className="text-accent-blue animate-spin" />,
    queued: <Clock size={14} className="text-gray-500" />,
  }[job.status] || <Clock size={14} className="text-gray-500" />;

  return (
    <div className="flex items-center gap-2 text-sm">
      {icon}
      <span className="text-gray-300 uppercase text-xs font-medium">{job.tool}</span>
      <StatusBadge status={job.status} />
      {job.findings_count > 0 && (
        <span className="text-xs text-gray-400">{job.findings_count} findings</span>
      )}
    </div>
  );
}

export default function ScanDetailPage() {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const eventSourceRef = useRef(null);

  const loadScan = () => scansApi.get(id).then((r) => setScan(r.data));
  const loadFindings = () => findingsApi.list({ scan_id: id }).then((r) => setFindings(r.data));

  useEffect(() => {
    Promise.all([loadScan(), loadFindings()]).finally(() => setLoading(false));

    const token = localStorage.getItem("vapt_token");
    const es = new EventSource(`/api/v1/scans/${id}/stream?token=${token}`);
    eventSourceRef.current = es;
    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setScan((prev) => prev ? { ...prev, status: data.status, progress: data.progress } : prev);
      if (["completed", "failed", "cancelled", "completed_with_errors"].includes(data.status)) {
        es.close();
        loadScan();
        loadFindings();
      }
    };
    return () => es.close();
  }, [id]);

  const handleCancel = async () => {
    await scansApi.cancel(id);
    loadScan();
  };

  if (loading) return <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader size={14} className="animate-spin" /> Loading…</div>;
  if (!scan) return <div className="text-red-400 text-sm">Scan not found.</div>;

  const sevCounts = { critical: 0, high: 0, medium: 0, low: 0, informational: 0 };
  findings.forEach((f) => { if (sevCounts[f.severity] !== undefined) sevCounts[f.severity]++; });

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-100">
          Scan <span className="font-mono text-gray-400 text-base">{scan.id.slice(0, 8)}</span>
        </h1>
        <div className="flex items-center gap-2">
          {["queued", "running"].includes(scan.status) && (
            <button onClick={handleCancel} className="btn-danger flex items-center gap-1 text-xs">
              <StopCircle size={12} /> Cancel
            </button>
          )}
          <Link to="/scans" className="btn-secondary text-xs">← Back</Link>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card"><div className="text-xs text-gray-500 mb-1">Status</div><StatusBadge status={scan.status} /></div>
        <div className="card"><div className="text-xs text-gray-500 mb-1">Profile</div><div className="text-sm text-gray-200">{scan.scan_profile?.replace(/_/g, " ")}</div></div>
        <div className="card"><div className="text-xs text-gray-500 mb-1">Intensity</div><div className="text-sm text-gray-200 capitalize">{scan.intensity}</div></div>
        <div className="card">
          <div className="text-xs text-gray-500 mb-1">Progress</div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-surface-600 rounded-full">
              <div className="h-2 bg-accent-blue rounded-full transition-all" style={{ width: `${scan.progress}%` }} />
            </div>
            <span className="text-xs text-gray-400">{scan.progress}%</span>
          </div>
        </div>
      </div>

      {/* Tool jobs */}
      <div className="card">
        <h2 className="text-sm font-medium text-gray-300 mb-3">Tool Execution</h2>
        <div className="space-y-2">
          {scan.jobs?.map((job) => <ToolStatus key={job.id} job={job} />) || (
            <p className="text-xs text-gray-500">No jobs yet.</p>
          )}
        </div>
      </div>

      {/* Finding summary */}
      <div className="card">
        <h2 className="text-sm font-medium text-gray-300 mb-3">Finding Summary</h2>
        <div className="grid grid-cols-5 gap-2 text-center">
          {["critical","high","medium","low","informational"].map((s) => (
            <div key={s} className={`p-2 rounded border badge-${s} flex flex-col items-center`}>
              <span className="text-lg font-bold">{sevCounts[s]}</span>
              <span className="text-xs mt-0.5 capitalize">{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Findings table */}
      {findings.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-medium text-gray-300 mb-3">Findings ({findings.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-surface-600">
                  <th className="pb-2 pr-4">Severity</th>
                  <th className="pb-2 pr-4">Title</th>
                  <th className="pb-2 pr-4">Tool</th>
                  <th className="pb-2 pr-4">Affected</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f) => (
                  <tr key={f.id} className="border-b border-surface-700/50 hover:bg-surface-700/20">
                    <td className="py-2 pr-4"><SeverityBadge severity={f.severity} /></td>
                    <td className="py-2 pr-4">
                      <Link to={`/findings/${f.id}`} className="text-gray-200 hover:text-accent-blue">
                        {f.title}
                      </Link>
                    </td>
                    <td className="py-2 pr-4 text-gray-400 text-xs uppercase">{f.source_tool}</td>
                    <td className="py-2 pr-4 text-gray-500 text-xs truncate max-w-[200px]">{f.affected_resource}</td>
                    <td className="py-2"><StatusBadge status={f.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
