import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../store/auth";
import {
  LayoutDashboard, Target, ScanLine, Bug,
  FileText, History, LogOut, Shield, ArrowLeftRight,
} from "lucide-react";
import clsx from "clsx";

const NAV = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/targets", icon: Target, label: "Targets" },
  { to: "/scans", icon: ScanLine, label: "Scans" },
  { to: "/findings", icon: Bug, label: "Findings" },
  { to: "/history", icon: History, label: "Scan History" },
  { to: "/reports", icon: FileText, label: "Reports" },
  { to: "/compare", icon: ArrowLeftRight, label: "Compare" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-surface-800 border-r border-surface-600 flex flex-col shrink-0">
        <div className="flex items-center gap-2 px-4 py-4 border-b border-surface-600">
          <Shield className="text-accent-blue" size={20} />
          <span className="text-sm font-semibold text-gray-100 tracking-wide">VAPT Platform</span>
        </div>

        <nav className="flex-1 py-4 space-y-0.5 px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-accent-blue/20 text-accent-blue border border-accent-blue/30"
                    : "text-gray-400 hover:text-gray-100 hover:bg-surface-700"
                )
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-surface-600 p-3">
          <div className="text-xs text-gray-500 mb-1 truncate">{user?.email}</div>
          <div className="text-xs text-gray-600 capitalize mb-2">{user?.role}</div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-accent-red transition-colors"
          >
            <LogOut size={12} /> Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
