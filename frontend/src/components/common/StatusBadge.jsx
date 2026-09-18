import clsx from "clsx";

const STATUS_COLORS = {
  queued: "text-gray-400 bg-gray-700/40 border-gray-600",
  running: "text-blue-300 bg-blue-900/30 border-blue-700/50 animate-pulse",
  completed: "text-green-300 bg-green-900/30 border-green-700/50",
  completed_with_errors: "text-yellow-300 bg-yellow-900/30 border-yellow-700/50",
  failed: "text-red-300 bg-red-900/30 border-red-700/50",
  cancelled: "text-gray-500 bg-gray-800/40 border-gray-700",
  open: "text-red-300 bg-red-900/30 border-red-700/50",
  assigned: "text-blue-300 bg-blue-900/30 border-blue-700/50",
  in_progress: "text-yellow-300 bg-yellow-900/30 border-yellow-700/50",
  fixed: "text-green-300 bg-green-900/30 border-green-700/50",
  retest_required: "text-purple-300 bg-purple-900/30 border-purple-700/50",
  closed: "text-gray-400 bg-gray-700/40 border-gray-600",
  false_positive: "text-gray-500 bg-gray-800/40 border-gray-700",
};

export default function StatusBadge({ status }) {
  const key = (status || "").toLowerCase().replace(" ", "_");
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        STATUS_COLORS[key] || "text-gray-400 bg-gray-700 border-gray-600"
      )}
    >
      {status?.replace(/_/g, " ").toUpperCase()}
    </span>
  );
}
