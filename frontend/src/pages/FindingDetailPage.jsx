import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { findingsApi, retestsApi } from "../services/api";
import { Loader, MessageSquare, History, RefreshCw } from "lucide-react";
import SeverityBadge from "../components/common/SeverityBadge";
import StatusBadge from "../components/common/StatusBadge";

const STATUSES = ["open", "assigned", "in_progress", "fixed", "retest_required", "closed", "false_positive"];

function Section({ title, children }) {
  return (
    <div>
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{title}</div>
      <div className="text-sm text-gray-300 bg-surface-700 rounded p-3 whitespace-pre-wrap">{children || "—"}</div>
    </div>
  );
}

export default function FindingDetailPage() {
  const { id } = useParams();
  const [finding, setFinding] = useState(null);
  const [notes, setNotes] = useState([]);
  const [history, setHistory] = useState([]);
  const [note, setNote] = useState("");
  const [updating, setUpdating] = useState(false);
  const [addingNote, setAddingNote] = useState(false);
  const [retests, setRetests] = useState([]);
  const [requestingRetest, setRequestingRetest] = useState(false);
  const [retestForm, setRetestForm] = useState({ retestId: null, stillVulnerable: true, resultSummary: "" });
  const [completingRetest, setCompletingRetest] = useState(false);

  const load = async () => {
    const [f, n, h, rt] = await Promise.all([
      findingsApi.get(id),
      findingsApi.getNotes(id),
      findingsApi.getHistory(id),
      retestsApi.list(id),
    ]);
    setFinding(f.data);
    setNotes(n.data);
    setHistory(h.data);
    setRetests(rt.data);
  };

  useEffect(() => { load(); }, [id]);

  const handleStatusChange = async (newStatus) => {
    setUpdating(true);
    await findingsApi.update(id, { status: newStatus });
    await load();
    setUpdating(false);
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!note.trim()) return;
    setAddingNote(true);
    await findingsApi.addNote(id, { note });
    setNote("");
    await load();
    setAddingNote(false);
  };

  const handleRequestRetest = async () => {
    setRequestingRetest(true);
    try {
      await retestsApi.request(id);
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to request retest");
    } finally {
      setRequestingRetest(false);
    }
  };

  const handleCompleteRetest = async (retestId) => {
    if (!retestForm.resultSummary.trim()) return;
    setCompletingRetest(true);
    try {
      await retestsApi.complete(retestId, {
        still_vulnerable: retestForm.stillVulnerable,
        result_summary: retestForm.resultSummary,
      });
      setRetestForm({ retestId: null, stillVulnerable: true, resultSummary: "" });
      await load();
    } finally {
      setCompletingRetest(false);
    }
  };

  const pendingRetest = retests.find((r) => r.status === "pending");

  if (!finding) return <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader size={14} className="animate-spin" /> Loading…</div>;

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-base font-semibold text-gray-100 max-w-2xl">{finding.title}</h1>
        <Link to="/findings" className="btn-secondary text-xs">← Back</Link>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <SeverityBadge severity={finding.severity} />
        <StatusBadge status={finding.status} />
        {finding.cve && <span className="font-mono text-xs text-gray-400">{finding.cve}</span>}
        {finding.cwe && <span className="font-mono text-xs text-gray-400">{finding.cwe}</span>}
        {finding.cvss_score && <span className="text-xs text-gray-400">CVSS {finding.cvss_score}</span>}
        <span className="text-xs text-gray-500 uppercase">{finding.source_tool}</span>
      </div>

      <div className="card space-y-4">
        <Section title="Affected Resource">{finding.affected_resource}</Section>
        <Section title="Description">{finding.description}</Section>
        <Section title="Evidence">{finding.evidence}</Section>
        <Section title="Impact">{finding.impact}</Section>
        <Section title="Recommendation">{finding.recommendation}</Section>
      </div>

      {/* Remediation workflow */}
      <div className="card">
        <h2 className="text-sm font-medium text-gray-300 mb-3">Remediation Status</h2>
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => handleStatusChange(s)}
              disabled={updating || s === finding.status}
              className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                s === finding.status
                  ? "border-accent-blue bg-accent-blue/20 text-accent-blue"
                  : "border-surface-500 text-gray-400 hover:border-surface-400 hover:text-gray-200"
              }`}
            >
              {s.replace(/_/g, " ").toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Notes */}
      <div className="card">
        <h2 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-1.5">
          <MessageSquare size={14} /> Remediation Notes ({notes.length})
        </h2>
        <div className="space-y-2 mb-3">
          {notes.map((n) => (
            <div key={n.id} className="bg-surface-700 rounded p-3">
              <div className="text-xs text-gray-500 mb-1">{n.author} · {new Date(n.created_at).toLocaleString()}</div>
              <div className="text-sm text-gray-300">{n.note}</div>
            </div>
          ))}
        </div>
        <form onSubmit={handleAddNote} className="flex gap-2">
          <input
            className="input flex-1"
            placeholder="Add a remediation note…"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <button type="submit" className="btn-primary text-xs" disabled={addingNote}>
            {addingNote ? "Saving…" : "Add"}
          </button>
        </form>
      </div>

      {/* Retests */}
      <div className="card">
        <h2 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-1.5">
          <RefreshCw size={14} /> Retests ({retests.length})
        </h2>
        {retests.length > 0 && (
          <div className="space-y-2 mb-3">
            {retests.map((rt) => (
              <div key={rt.id} className="bg-surface-700 rounded p-3 text-xs">
                <div className="flex items-center gap-3 mb-1">
                  <span className={`font-semibold ${rt.status === "completed" ? (rt.still_vulnerable ? "text-accent-red" : "text-green-400") : "text-yellow-400"}`}>
                    {rt.status === "completed"
                      ? rt.still_vulnerable ? "Still Vulnerable" : "Fixed"
                      : "Pending"}
                  </span>
                  <span className="text-gray-500">requested by {rt.requested_by}</span>
                  <span className="text-gray-600">{new Date(rt.created_at).toLocaleDateString()}</span>
                </div>
                {rt.result_summary && <div className="text-gray-400">{rt.result_summary}</div>}
                {rt.status === "pending" && retestForm.retestId === rt.id && (
                  <div className="mt-2 space-y-2">
                    <div className="flex gap-3 items-center">
                      <label className="flex items-center gap-1 text-gray-400">
                        <input type="radio" checked={retestForm.stillVulnerable} onChange={() => setRetestForm((f) => ({ ...f, stillVulnerable: true }))} />
                        Still vulnerable
                      </label>
                      <label className="flex items-center gap-1 text-gray-400">
                        <input type="radio" checked={!retestForm.stillVulnerable} onChange={() => setRetestForm((f) => ({ ...f, stillVulnerable: false }))} />
                        Fixed
                      </label>
                    </div>
                    <input
                      className="input w-full"
                      placeholder="Retest result summary…"
                      value={retestForm.resultSummary}
                      onChange={(e) => setRetestForm((f) => ({ ...f, resultSummary: e.target.value }))}
                    />
                    <div className="flex gap-2">
                      <button className="btn-primary text-xs" onClick={() => handleCompleteRetest(rt.id)} disabled={completingRetest}>
                        {completingRetest ? "Saving…" : "Submit result"}
                      </button>
                      <button className="btn-secondary text-xs" onClick={() => setRetestForm({ retestId: null, stillVulnerable: true, resultSummary: "" })}>
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
                {rt.status === "pending" && retestForm.retestId !== rt.id && (
                  <button className="btn-secondary text-xs mt-2" onClick={() => setRetestForm({ retestId: rt.id, stillVulnerable: true, resultSummary: "" })}>
                    Record result
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        {!pendingRetest && (
          <button
            className="btn-secondary text-xs flex items-center gap-1"
            onClick={handleRequestRetest}
            disabled={requestingRetest}
          >
            <RefreshCw size={11} /> {requestingRetest ? "Requesting…" : "Request retest"}
          </button>
        )}
      </div>

      {/* Status history */}
      {history.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-1.5">
            <History size={14} /> Status History
          </h2>
          <div className="space-y-1.5">
            {history.map((h) => (
              <div key={h.id} className="text-xs text-gray-400 flex items-center gap-2">
                <span className="text-gray-600">{new Date(h.changed_at).toLocaleString()}</span>
                <span>{h.changed_by}</span>
                <span className="text-gray-600">→</span>
                <StatusBadge status={h.new_status} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
