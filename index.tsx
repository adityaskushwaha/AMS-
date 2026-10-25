import { createFileRoute, Link } from "@tanstack/react-router";
import { Shell, RateBadge } from "@/components/Shell";
import { AIPanel } from "@/components/AIPanel";
import { departments, allClasses, pastDays, todayKey } from "@/lib/data";
import { useRecords, classRate, avgClassRate, summaryForAI, isMarked } from "@/lib/attendance";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AMS — AI Driven Attendance Monitoring System" },
      { name: "description", content: "Monitor every department and class attendance with AI insights." },
      { property: "og:title", content: "AMS — AI Driven Attendance Monitoring System" },
      { property: "og:description", content: "Monitor every department and class attendance with AI insights." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const r = useRecords();
  const today = todayKey();
  const days = pastDays(14);
  const overall = allClasses.reduce((a, c) => a + avgClassRate(r, c), 0) / allClasses.length;
  const markedToday = allClasses.filter((c) => isMarked(r, c.id, today)).length;
  const atRisk = allClasses.filter((c) => avgClassRate(r, c) < 80).length;
  const trend = days.map((d) => {
    const vals = allClasses.map((c) => classRate(r, c, d)).filter((v): v is number => v !== null);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  });

  return (
    <Shell>
      <header>
        <p className="eyebrow">Dashboard</p>
        <h1 className="text-2xl font-semibold md:text-3xl">Attendance overview</h1>
      </header>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Overall (14 days)" value={`${overall.toFixed(1)}%`} />
        <Stat label="Students" value={String(allClasses.length * 60)} />
        <Stat label="Classes marked today" value={`${markedToday} / ${allClasses.length}`} />
        <Stat label="Classes below 80%" value={String(atRisk)} />
      </div>

      <section className="section-block mt-8">
        <h2 className="text-lg font-semibold">Fourteen-day trend</h2>
        <div className="mt-6 flex h-40 items-end gap-2">
          {trend.map((v, i) => (
            <div key={i} className="flex flex-1 flex-col items-center gap-1">
              <div className="bar w-full" style={{ height: `${Math.max(v, 2) * 1.4}px` }} title={`${days[i]}: ${v.toFixed(0)}%`} />
              <span className="text-[10px] text-muted-foreground">{days[i]?.slice(8)}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          {departments.map((d) => (
            <section key={d.id} className="section-block">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-lg font-semibold">{d.name}</h2>
                <Link to="/departments/$deptId" params={{ deptId: d.id }} className="link">View classes →</Link>
              </div>
              <table className="mt-4 w-full text-left">
                <thead className="text-xs text-muted-foreground">
                  <tr><th className="py-2">Class</th><th>Today</th><th>14-day avg</th><th></th></tr>
                </thead>
                <tbody>
                  {d.classes.map((c) => (
                    <tr key={c.id} className="border-t">
                      <td className="py-3 font-medium">{c.name}</td>
                      <td><RateBadge v={classRate(r, c, today)} /></td>
                      <td><RateBadge v={avgClassRate(r, c)} /></td>
                      <td className="text-right"><Link to="/classes/$classId" params={{ classId: c.id }} className="link">Mark</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ))}
        </div>
        <div className="lg:sticky lg:top-6 h-fit">
          <AIPanel
            context={() => summaryForAI(r)}
            suggestions={["Which classes need attention?", "Summarize today's attendance", "Compare departments"]}
          />
        </div>
      </div>
    </Shell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel p-5">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
    </div>
  );
}
