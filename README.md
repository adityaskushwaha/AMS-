# AMS — AI Driven Attendance Monitoring System

AMS is a web-based attendance monitoring system for a private-university-style campus. It organizes students into **Departments → Classes → Students** and gives staff a live dashboard that monitors every class, with an AI assistant built in to answer questions about attendance at-risk students.

---

## Features

### 📊 Dashboard (monitor every class)
- Campus-wide stats at a glance: overall attendance % (last 14 days), total students, classes marked today, and classes below the 80% threshold.
- 14-day attendance trend chart.
- Per-department tables showing today's rate and the 14-day average for every class, with quick links to mark attendance.
- Color-coded health badges (good / warning / at-risk) on every rate.

### 🗂 Department folders
- Four departments: **Computer Science (CSE)**, **Electronics & Communication (ECE)**, **Mechanical Engineering (ME)**, **Civil Engineering (CIV)**.
- Each department holds three classes (Year I, II, III) — 12 classes total.
- Every class card shows today's status and the rolling average.

### ✅ Attendance marking
- Date picker (cannot mark future dates) with a 60-student roster per class.
- One-tap **Present / Absent** toggle per student, plus **All Present / All Absent** shortcuts.
- Each student row shows their personal 30-day attendance rate; students below **75%** are highlighted as at-risk.
- Save per day per class; the day is locked in once marked.

### 🤖 AI Insights
- An AI panel is available on the dashboard and on every class page.
- Ask questions in plain language ("Which classes need attention?", "Who is at risk in CSE Year II?").
- The AI flags students below 75% and classes below thresholds automatically.
- Powered by the Lovable AI Gateway.

### 🔢 Student roll numbers
- Every student has a unique sequential roll number from **202410101150001** through **202410101150720**.
- A test guards this invariant, so the roster always stays unique and ordered.

### 🎨 Clean university-style UI
- Simple, plain sans-serif layout with neutral white/gray surfaces.
- Color reserved for action buttons and status badges.
- Subtle gradients on class pages to keep things engaging.
- Custom app icon (person-with-checkmark) with a pink-to-green gradient in the sidebar and browser tab.

---

## Tech Stack

- **TanStack Start** (React 19, SSR-ready, server functions)
- **TypeScript**
- **Tailwind CSS v4**
- **Lovable AI Gateway** for AI insights

---

## Project Structure

```
src/
├── routes/
│   ├── index.tsx              # Dashboard — campus-wide monitoring
│   ├── departments.$deptId.tsx  # Department folder → class cards
│   └── classes.$classId.tsx   # Class page — mark attendance, AI panel
├── components/
│   ├── Shell.tsx              # Sidebar, logo, navigation
│   └── AIPanel.tsx            # AI insights panel
├── lib/
│   ├── data.ts                # Dataset generator (departments, classes, students)
│   ├── attendance.ts          # Attendance store (localStorage-backed)
│   └── ai.functions.ts        # AI server function
└── test/
    └── student-rolls.test.ts  # Roll number uniqueness/sequence test
```

---

## Dataset

The app ships with a **deterministically generated sample dataset** so the dashboard is populated from first run — no backend required.

### Structure

| Level | Count | Details |
|---|---|---|
| Departments | 4 | CSE, ECE, ME, CIV |
| Classes | 12 | 3 year-groups per department |
| Students per class | 60 | — |
| Total students | 720 | Unique roll numbers 202410101150001–202410101150720 |
| Attendance history | 14 days | Seeded per student per day |

### Student fields

| Field | Example |
|---|---|
| Roll No | `202410101150001` |
| Student Name | `Rahul Chopra` |
| Class | `CSE Year I` |
| Department | `Computer Science` |

### Attendance fields

| Field | Example |
|---|---|
| Date | `2026-10-15` |
| Status | `P` (present) / `A` (absent) |
| Days Present | `13` |
| Present % | `92.9` |

### How the sample data is generated

- Student names are drawn from a fixed first/last name pool using a seeded hash, so every run produces the same 720 students.
- Historical attendance is seeded per student: each student has a fixed base attendance likelihood (68–98%), and each day is derived from a hash of `studentId + date`. This makes the history stable, realistic, and reproducible — same student, same day, same result.
- Attendance you mark in the app (for today or past dates) is saved on top of this seed and takes precedence.

### Exported dataset files

The full dataset is also available as standalone files (generated from the same source the app reads):

| File | Contents |
|---|---|
| `AMS_Dataset.xlsx` | 3 sheets: Students (720 rows), Attendance 14-day P/A matrix with per-student totals and %, Classes (12 rows) |
| `AMS_Students.csv` | Student roster: roll no, name, class, department |
| `AMS_Attendance_14days.csv` | One row per student, one P/A column per date |

> **Note:** This is sample data. Real student rosters can be swapped in by editing `src/lib/data.ts` (names/classes) or by wiring the store to a database for shared, multi-device persistence.

---

## Data Storage

Attendance records are stored client-side in the browser's **localStorage** (key `ams-attendance-v1`), so no setup is needed. Sample history is computed deterministically; anything you mark yourself is persisted locally in the browser that marked it.

---

## Getting Started

```sh
npm i
npm run dev
```

## Running Tests

```sh
bunx vitest run
```

## Built with

- TanStack Start
- TypeScript
- React
- Tailwind CSS
