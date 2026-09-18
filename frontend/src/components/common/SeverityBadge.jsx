export default function SeverityBadge({ severity }) {
  const s = (severity || "").toLowerCase();
  return <span className={`badge-${s}`}>{severity?.toUpperCase()}</span>;
}
