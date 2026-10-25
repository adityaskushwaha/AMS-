import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import logo from "@/assets/app-icon.png";
import { departments } from "@/lib/data";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen md:flex">
      <aside className="sidebar md:w-60 md:shrink-0 md:min-h-screen p-5">
        <Link to="/" className="flex items-center gap-3">
          <img src={logo} alt="AMS logo" width={48} height={48} className="h-12 w-12" />
          <div>
            <div className="text-xl font-semibold">AMS</div>
            <div className="text-xs text-muted-foreground">Attendance Monitor</div>
          </div>
        </Link>
        <nav className="mt-7 space-y-1">
          <Link to="/" className="nav-link" activeOptions={{ exact: true }} activeProps={{ className: "nav-link active" }}>Dashboard</Link>
          <div className="pt-5 pb-2 px-3 text-xs font-semibold text-muted-foreground">Departments</div>
          {departments.map((d) => (
            <Link key={d.id} to="/departments/$deptId" params={{ deptId: d.id }} className="nav-link" activeProps={{ className: "nav-link active" }}>
              {d.name}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="min-w-0 flex-1 p-5 md:p-8">{children}</main>
    </div>
  );
}

export function RateBadge({ v }: { v: number | null }) {
  if (v === null) return <span className="badge badge-muted">Not marked</span>;
  const cls = v >= 85 ? "badge-good" : v >= 75 ? "badge-warn" : "badge-bad";
  return <span className={`badge ${cls}`}>{v.toFixed(0)}%</span>;
}
