import { useState, useEffect } from "react";
import { dashboardApi } from "../services/api";
import { Link } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { ScanLine, Bug, Target, CheckCircle, AlertTriangle, Loader } from "lucide-react";
import StatusBadge from "../components/common/StatusBadge";

const SEV_COLORS = {
  critical: "#f85149",
  high: "#db6d28",
  medium: "#d29922",
  low: "#2f81f7",
  informational: "#6e7681",
};

function StatCard({ label, value, icon: Icon, color = "text-gray-100", sub }) {
  return (
    <div className="card flex items-start gap-3">
      <div className={`mt-0.5 ${color}`}>
        <Icon size={18} />
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-100">{value ?? "—"}</div>
        <div className="text-xs text-gray-400 mt-0.5">{label}</div>
        {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.summary().then((r) => setData(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center gap-2 text-gray-400 text-sm">
      <Loader size={14} className="animate-spin" /> Loading dashboard…
    </div>
  );

  if (!data) return <div className="text-red-400 text-sm">Failed to load dashboard.</div>;

  const severityChart = ["critical", "high", "medium", "low", "informational"].map((s) => ({
    name: s,
    value: data.findings[s] || 0,
    fill: SEV_COLORS[s],
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-100">Security Dashboard</h1>
        <Link to="/scans/new" className="btn-primary text-xs">+ New Scan</Link>
      </div>

      {/* Scan stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Scans" value={data.scans.total} icon={ScanLine} />
        <StatCard label="Running" value={data.scans.running} icon={Loader} color="text-accent-blue" />
        <StatCard label="Completed" value={data.scans.completed} icon={CheckCircle} color="text-accent-green" />
        <StatCard label="Failed" value={data.scans.failed} icon={AlertTriangle} color="text-accent-red" />
      </div>

      {/* Finding stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Open Findings" value={data.findings.total} icon={Bug} color="text-accent-red" />
        <StatCard label="Critical" value={data.findings.critical} icon={Bug} color="text-red-400" />
        <StatCard label="High" value={data.findings.high} icon={Bug} color="text-orange-400" />
        <StatCard label="Medium" value={data.findings.medium} icon={Bug} color="text-yellow-400" />
        <StatCard label="Remediated" value={data.findings.remediated} icon={CheckCircle} color="text-accent-green" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Severity distribution */}
        <div className="card">
          <h2 className="text-sm font-medium text-gray-300 mb-3">Severity Distribution</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={severityChart} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#6e7681" }} />
              <YAxis tick={{ fontSize: 10, fill: "#6e7681" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: 4 }}
                labelStyle={{ color: "#c9d1d9" }}
                itemStyle={{ color: "#c9d1d9" }}
              />
              <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                {severityChart.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Most affected assets */}
        <div className="card">
          <h2 className="text-sm font-medium text-gray-300 mb-3">Most Affected Assets</h2>
          {data.most_affected_assets.length === 0 ? (
            <p className="text-xs text-gray-500">No findings yet.</p>
          ) : (
            <div className="space-y-2">
              {data.most_affected_assets.map((a, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300 truncate max-w-[200px]">{a.target}</span>
                  <span className="text-sm font-bold text-accent-red">{a.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent scans */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-300">Recent Scans</h2>
          <Link to="/history" className="text-xs text-accent-blue hover:underline">View all</Link>
        </div>
        {data.recent_scans.length === 0 ? (
          <p className="text-xs text-gray-500">No scans yet. <Link to="/scans/new" className="text-accent-blue hover:underline">Start a scan</Link>.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-surface-600">
                  <th className="pb-2 pr-4">Target</th>
                  <th className="pb-2 pr-4">Profile</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2">Started</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_scans.map((scan) => (
                  <tr key={scan.id} className="border-b border-surface-700/50 hover:bg-surface-700/20">
                    <td className="py-2 pr-4 text-gray-300">{scan.target}</td>
                    <td className="py-2 pr-4 text-gray-400">{scan.profile?.replace(/_/g, " ")}</td>
                    <td className="py-2 pr-4"><StatusBadge status={scan.status} /></td>
                    <td className="py-2 text-gray-500 text-xs">
                      {scan.created_at ? new Date(scan.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
