import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { Folder } from "lucide-react";
import { Shell, RateBadge } from "@/components/Shell";
import { getDept, todayKey } from "@/lib/data";
import { useRecords, classRate, avgClassRate } from "@/lib/attendance";

export const Route = createFileRoute("/departments/$deptId")({
  loader: ({ params }) => {
    const d = getDept(params.deptId);
    if (!d) throw notFound();
    return { name: d.name };
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: `${loaderData?.name ?? "Department"} — AMS` },
      { name: "description", content: `Classes and attendance for ${loaderData?.name}.` },
      { property: "og:title", content: `${loaderData?.name ?? "Department"} — AMS` },
      { property: "og:description", content: `Classes and attendance for ${loaderData?.name}.` },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: DeptPage,
});

function DeptPage() {
  const { deptId } = Route.useParams();
  const d = getDept(deptId)!;
  const r = useRecords();
  return (
    <Shell>
      <p className="eyebrow">Department</p>
      <h1 className="text-2xl font-semibold md:text-3xl">{d.name}</h1>
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {d.classes.map((c) => (
          <Link key={c.id} to="/classes/$classId" params={{ classId: c.id }} className="panel panel-hover p-6 block">
            <Folder className="h-7 w-7 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">{c.name}</h2>
            <p className="text-sm text-muted-foreground">60 students</p>
            <div className="mt-4 flex gap-3 text-sm">
              <span>Today <RateBadge v={classRate(r, c, todayKey())} /></span>
              <span>Avg <RateBadge v={avgClassRate(r, c)} /></span>
            </div>
          </Link>
        ))}
      </div>
    </Shell>
  );
}
