import { useState, useEffect } from "react";
import { scansApi, reportsApi } from "../services/api";
import { FileDown, Loader, FilePlus } from "lucide-react";

export default function ReportsPage() {
  const [scans, setScans] = useState([]);
  const [selectedScan, setSelectedScan] = useState("");
  const [reports, setReports] = useState([]);
  const [summary, setSummary] = useState("");
  const [generating, setGenerating] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);

  useEffect(() => {
    scansApi.list().then((r) => {
      const completed = r.data.filter((s) =>
        ["completed", "completed_with_errors"].includes(s.status)
      );
      setScans(completed);
    });
  }, []);

  const loadReports = async (scanId) => {
    if (!scanId) return;
    setLoadingReports(true);
    const r = await reportsApi.list(scanId);
    setReports(r.data);
    setLoadingReports(false);
  };

  const handleScanChange = (e) => {
    setSelectedScan(e.target.value);
    loadReports(e.target.value);
    setReports([]);
  };

  const handleGenerate = async () => {
    if (!selectedScan) return;
    setGenerating(true);
    try {
      await reportsApi.generate(selectedScan, { executive_summary: summary || null });
      await loadReports(selectedScan);
      setSummary("");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (reportId, scanId, version) => {
    const res = await reportsApi.download(reportId);
    const url = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `vapt_report_${scanId.slice(0, 8)}_v${version}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-base font-semibold text-gray-100">Reports</h1>

      <div className="card space-y-4">
        <h2 className="text-sm font-medium text-gray-300">Generate PDF Report</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Select completed scan</label>
            <select className="input w-full" value={selectedScan} onChange={handleScanChange}>
              <option value="">— choose a scan —</option>
              {scans.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id.slice(0, 8)} · {s.scan_profile} · {s.status}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Executive summary (optional)</label>
            <textarea
              className="input w-full h-24 resize-none"
              placeholder="Briefly describe the engagement scope, risk posture, and key conclusions…"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
            />
          </div>
          <button
            className="btn-primary text-xs flex items-center gap-1.5"
            onClick={handleGenerate}
            disabled={!selectedScan || generating}
          >
            {generating ? <Loader size={12} className="animate-spin" /> : <FilePlus size={12} />}
            {generating ? "Generating…" : "Generate PDF"}
          </button>
        </div>
      </div>

      {selectedScan && (
        <div className="card">
          <h2 className="text-sm font-medium text-gray-300 mb-3">Report History</h2>
          {loadingReports ? (
            <div className="flex items-center gap-2 text-xs text-gray-400"><Loader size={12} className="animate-spin" /> Loading…</div>
          ) : reports.length === 0 ? (
            <p className="text-xs text-gray-500">No reports generated for this scan yet.</p>
          ) : (
            <div className="space-y-2">
              {reports.map((r) => (
                <div key={r.id} className="flex items-center justify-between bg-surface-700 rounded px-3 py-2">
                  <div>
                    <span className="text-sm text-gray-200">v{r.version}</span>
                    <span className="text-xs text-gray-500 ml-2">{new Date(r.created_at).toLocaleString()}</span>
                    <span className="text-xs text-gray-600 ml-2">by {r.generated_by}</span>
                  </div>
                  <button
                    className="btn-secondary text-xs flex items-center gap-1"
                    onClick={() => handleDownload(r.id, r.scan_id, r.version)}
                  >
                    <FileDown size={12} /> Download
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
