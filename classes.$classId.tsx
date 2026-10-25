import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { Shell } from "@/components/Shell";
import { AIPanel } from "@/components/AIPanel";
import { Button } from "@/components/ui/button";
import { getClass, getDept, todayKey } from "@/lib/data";
import { useRecords, saveDay, present, studentRate, summaryForAI } from "@/lib/attendance";

export const Route = createFileRoute("/classes/$classId")({
  loader: ({ params }) => {
    const c = getClass(params.classId);
    if (!c) throw notFound();
    return { name: c.name };
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: `${loaderData?.name ?? "Class"} attendance — AMS` },
      { name: "description", content: `Mark and review attendance for ${loaderData?.name}.` },
      { property: "og:title", content: `${loaderData?.name ?? "Class"} attendance — AMS` },
      { property: "og:description", content: `Mark and review attendance for ${loaderData?.name}.` },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: ClassPage,
});

function ClassPage() {
  const { classId } = Route.useParams();
  const c = getClass(classId)!;
  const d = getDept(c.deptId)!;
  const r = useRecords();
  const [date, setDate] = useState(todayKey());
  const [marks, setMarks] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const m: Record<string, boolean> = {};
    for (const s of c.students) m[s.id] = present(r, c.id, s.id, date) ?? true;
    setMarks(m);
    setSaved(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date, classId]);

  const count = Object.values(marks).filter(Boolean).length;
  const setAll = (v: boolean) => setMarks(Object.fromEntries(c.students.map((s) => [s.id, v])));

  return (
    <Shell>
      <header className="class-heading -mx-5 -mt-5 md:-mx-8 md:-mt-8">
        <Link to="/departments/$deptId" params={{ deptId: d.id }} className="link text-sm">← {d.name}</Link>
        <h1 className="mt-2 text-2xl font-semibold md:text-3xl">{c.name}</h1>
        <p className="mt-2 text-sm text-muted-foreground">60 students</p>
      </header>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input type="date" value={date} max={todayKey()} onChange={(e) => setDate(e.target.value)} className="field" />
        <Button variant="success" onClick={() => setAll(true)}><Check />All present</Button>
        <Button variant="destructive" onClick={() => setAll(false)}><X />All absent</Button>
        <span className="text-sm font-semibold">{count} / 60 present</span>
        <Button onClick={() => { saveDay(c.id, date, marks); setSaved(true); }} className="ml-auto">
          {saved ? "Saved ✓" : "Save attendance"}
        </Button>
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="class-students grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
          {c.students.map((s) => {
            const p = marks[s.id];
            const rate = studentRate(r, c, s.id);
            return (
              <Button variant="outline" aria-pressed={Boolean(p)}
                key={s.id}
                onClick={() => { setMarks({ ...marks, [s.id]: !p }); setSaved(false); }}
                className={`student h-auto whitespace-normal ${p ? "is-present" : "is-absent"}`}
              >
                <span className="min-w-0 flex-1 text-left">
                  <span className="block font-medium">{s.name}</span>
                  <span className="student-roll">Roll no. {s.roll}</span>
                  <span className="text-xs text-muted-foreground">{rate.toFixed(0)}% over 30 days</span>
                </span>
                {p ? <Check className="h-5 w-5" /> : <X className="h-5 w-5" />}
              </Button>
            );
          })}
        </div>
        <div className="lg:sticky lg:top-6 h-fit">
          <AIPanel
            context={() => summaryForAI(r, c.id)}
            suggestions={["Who is at risk?", "Draft a note for absent students", "Class attendance summary"]}
          />
        </div>
      </div>
    </Shell>
  );
}
