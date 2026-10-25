import { useSyncExternalStore } from "react";
import { allClasses, getClass, pastDays, seededPresent, todayKey, type ClassRoom } from "./data";

type Records = Record<string, Record<string, boolean>>; // `${classId}|${date}` -> studentId -> present
const KEY = "ams-attendance-v1";
let records: Records = {};
let loaded = false;
const listeners = new Set<() => void>();

function load() {
  if (loaded || typeof window === "undefined") return;
  loaded = true;
  try { records = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { records = {}; }
}
function emit() {
  localStorage.setItem(KEY, JSON.stringify(records));
  records = { ...records };
  listeners.forEach((l) => l());
}

export function useRecords() {
  return useSyncExternalStore(
    (l) => { load(); listeners.add(l); return () => listeners.delete(l); },
    () => { load(); return records; },
    () => ({}) as Records,
  );
}

export function saveDay(classId: string, date: string, marks: Record<string, boolean>) {
  records[`${classId}|${date}`] = marks;
  emit();
}

export function isMarked(r: Records, classId: string, date: string) {
  return !!r[`${classId}|${date}`];
}

export function present(r: Records, classId: string, studentId: string, date: string) {
  const day = r[`${classId}|${date}`];
  if (day && studentId in day) return day[studentId];
  if (date === todayKey()) return undefined; // today unmarked
  return seededPresent(studentId, date);
}

export function classRate(r: Records, c: ClassRoom, date: string) {
  let p = 0, n = 0;
  for (const s of c.students) {
    const v = present(r, c.id, s.id, date);
    if (v === undefined) continue;
    n++; if (v) p++;
  }
  return n ? (p / n) * 100 : null;
}

export function studentRate(r: Records, c: ClassRoom, studentId: string, days = 30) {
  const ds = pastDays(days);
  let p = 0, n = 0;
  for (const d of ds) {
    const v = present(r, c.id, studentId, d);
    if (v === undefined) continue;
    n++; if (v) p++;
  }
  return n ? (p / n) * 100 : 0;
}

export function avgClassRate(r: Records, c: ClassRoom, days = 14) {
  const vals = pastDays(days).map((d) => classRate(r, c, d)).filter((v): v is number => v !== null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
}

export function summaryForAI(r: Records, classId?: string) {
  if (classId) {
    const c = getClass(classId)!;
    const rows = c.students.map((s) => `#${s.roll} ${s.name}: ${studentRate(r, c, s.id).toFixed(0)}%`);
    return `Class ${c.name}, 30-day attendance per student:\n${rows.join("\n")}`;
  }
  return allClasses
    .map((c) => `${c.name}: 14-day avg ${avgClassRate(r, c).toFixed(1)}%, today ${classRate(r, c, todayKey())?.toFixed(0) ?? "not marked"}`)
    .join("\n");
}
