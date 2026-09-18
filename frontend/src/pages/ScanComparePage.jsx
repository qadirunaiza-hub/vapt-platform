import { useState, useEffect } from "react";
import { scansApi } from "../services/api";
import { Loader, ArrowLeftRight } from "lucide-react";
import SeverityBadge from "../components/common/SeverityBadge";

function FindingRow({ f }) {
  return (
    <div className="flex items-start gap-2 py-2 border-b border-surface-600 last:border-0">
      <SeverityBadge severity={f.severity} />
      <div className="flex-1 min-w-0">
        <div className="text-sm text-gray-200 truncate">{f.title}</div>
        {f.affected_resource && (
          <div className="text-xs text-gray-500 truncate">{f.affected_resource}</div>
        )}
      </div>
      <span className="text-xs text-gray-500 shrink-0">{f.source_tool}</span>
    </div>
  );
}

function Section({ title, color, items }) {
  return (
    <div className="card">
      <h3 className={`text-sm font-medium mb-3 ${color}`}>
        {title} <span className="text-gray-500 font-normal">({items.length})</span>
      </h3>
      {items.length === 0 ? (
        <p className="text-xs text-gray-500">None.</p>
      ) : (
        <div>{items.map((f) => <FindingRow key={f.id} f={f} />)}</div>
      )}
    </div>
  );
}

export default function ScanComparePage() {
  const [scans, setScans] = useState([]);
  const [scanA, setScanA] = useState("");
  const [scanB, setScanB] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    scansApi.list().then((r) =>
      setScans(r.data.filter((s) => ["completed", "completed_with_errors"].includes(s.status)))
    );
  }, []);

  const handleCompare = async () => {
    if (!scanA || !scanB || scanA === scanB) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await scansApi.compare(scanA, scanB);
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  const scanLabel = (id) => {
    const s = scans.find((x) => x.id === id);
    return s ? `${s.id.slice(0, 8)} · ${s.scan_profile}` : id;
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-base font-semibold text-gray-100">Scan Comparison</h1>

      <div className="card space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Baseline scan (A)</label>
            <select className="input w-full" value={scanA} onChange={(e) => setScanA(e.target.value)}>
              <option value="">— select —</option>
              {scans.map((s) => (
                <option key={s.id} value={s.id}>{s.id.slice(0, 8)} · {s.scan_profile}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Comparison scan (B)</label>
            <select className="input w-full" value={scanB} onChange={(e) => setScanB(e.target.value)}>
              <option value="">— select —</option>
              {scans.filter((s) => s.id !== scanA).map((s) => (
                <option key={s.id} value={s.id}>{s.id.slice(0, 8)} · {s.scan_profile}</option>
              ))}
            </select>
          </div>
        </div>
        <button
          className="btn-primary text-xs flex items-center gap-1.5"
          onClick={handleCompare}
          disabled={!scanA || !scanB || scanA === scanB || loading}
        >
          {loading ? <Loader size={12} className="animate-spin" /> : <ArrowLeftRight size={12} />}
          {loading ? "Comparing…" : "Compare scans"}
        </button>
        {error && <p className="text-xs text-accent-red">{error}</p>}
      </div>

      {result && (
        <div className="space-y-3">
          {/* Summary bar */}
          <div className="card flex gap-6">
            <div className="text-center">
              <div className="text-xl font-bold text-accent-red">{result.summary.new}</div>
              <div className="text-xs text-gray-500">New</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-400">{result.summary.resolved}</div>
              <div className="text-xs text-gray-500">Resolved</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-yellow-400">{result.summary.persisting}</div>
              <div className="text-xs text-gray-500">Persisting</div>
            </div>
            <div className="ml-auto text-xs text-gray-500 self-center text-right">
              <div>{scanLabel(result.scan_a_id)} → A</div>
              <div>{scanLabel(result.scan_b_id)} → B</div>
            </div>
          </div>

          <Section title="New findings (in B, not in A)" color="text-accent-red" items={result.new_findings} />
          <Section title="Resolved findings (in A, not in B)" color="text-green-400" items={result.resolved_findings} />
          <Section title="Persisting findings (in both)" color="text-yellow-400" items={result.persisting_findings} />
        </div>
      )}
    </div>
  );
}
