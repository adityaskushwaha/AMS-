export type Student = { id: string; roll: string; name: string };
export type ClassRoom = { id: string; name: string; deptId: string; students: Student[] };
export type Department = { id: string; name: string; short: string; classes: ClassRoom[] };

const FIRST = ["Aarav","Vivaan","Aditya","Ananya","Diya","Ishaan","Kavya","Rohan","Saanvi","Arjun","Meera","Kabir","Riya","Vihaan","Anika","Dev","Tara","Aryan","Nisha","Karan","Pooja","Rahul","Sneha","Yash","Zara","Neel","Isha","Om","Priya","Sahil"];
const LAST = ["Sharma","Verma","Iyer","Patel","Reddy","Nair","Gupta","Singh","Rao","Das","Mehta","Joshi","Kapoor","Menon","Bose","Kulkarni","Pillai","Chopra","Shah","Banerjee"];

const DEPTS = [
  { id: "cse", name: "Computer Science", short: "CSE" },
  { id: "ece", name: "Electronics & Communication", short: "ECE" },
  { id: "me", name: "Mechanical Engineering", short: "ME" },
  { id: "civ", name: "Civil Engineering", short: "CIV" },
];
const YEARS = ["I", "II", "III"];

function rand(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export const departments: Department[] = DEPTS.map((d, di) => ({
  ...d,
  classes: YEARS.map((y, yi) => {
    const id = `${d.id}-${yi + 1}`;
    return {
      id,
      deptId: d.id,
      name: `${d.short} Year ${y}`,
      students: Array.from({ length: 60 }, (_, i) => {
        const s = di * 1000 + yi * 100 + i;
        return {
          id: `${id}-${i + 1}`,
          roll: `202410101150${String((di * YEARS.length + yi) * 60 + i + 1).padStart(3, "0")}`,
          name: `${FIRST[Math.floor(rand(s + 1) * FIRST.length)]} ${LAST[Math.floor(rand(s + 7) * LAST.length)]}`,
        };
      }),
    };
  }),
}));

export const allClasses = departments.flatMap((d) => d.classes);
export const getDept = (id: string) => departments.find((d) => d.id === id);
export const getClass = (id: string) => allClasses.find((c) => c.id === id);

export const todayKey = () => new Date().toISOString().slice(0, 10);
export function pastDays(n: number) {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (n - 1 - i));
    return d.toISOString().slice(0, 10);
  });
}

/** Seeded history so the dashboard has data before anyone marks attendance. */
export function seededPresent(studentId: string, date: string) {
  let h = 0;
  for (const c of studentId + date) h = (h * 31 + c.charCodeAt(0)) | 0;
  let base = 0;
  for (const c of studentId) base = (base * 17 + c.charCodeAt(0)) | 0;
  const chance = 0.68 + rand(base) * 0.3; // each student 68–98% likely
  return rand(h) < chance;
}
