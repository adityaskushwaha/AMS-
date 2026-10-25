"""
Student Attendance App (desktop GUI)
------------------------------------
Libraries: tkinter (UI), sqlite3 (storage), pandas (reports/export)

Run:   python attendance_app.py
Needs: pip install pandas      (tkinter ships with Python)
"""

import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

import pandas as pd

DB_FILE = "attendance.db"

# ---------- Design tokens ----------
BG = "#F4F6FB"
SIDEBAR = "#1F2540"
SIDEBAR_HOVER = "#2D3558"
SIDEBAR_ACTIVE = "#4F6BED"
CARD = "#FFFFFF"
TEXT = "#1B1F3B"
MUTED = "#7A819C"
PRIMARY = "#4F6BED"
GREEN = "#22A06B"
RED = "#E5484D"
AMBER = "#F5A524"
BORDER = "#E3E7F1"

FONT = "Segoe UI"
STATUS_COLORS = {"Present": GREEN, "Late": AMBER, "Absent": RED}


# ---------- Database ----------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                roll_no TEXT PRIMARY KEY,
                name    TEXT NOT NULL,
                class   TEXT
            );
            CREATE TABLE IF NOT EXISTS attendance (
                roll_no TEXT NOT NULL,
                date    TEXT NOT NULL,
                status  TEXT NOT NULL CHECK (status IN ('Present','Absent','Late')),
                PRIMARY KEY (roll_no, date),
                FOREIGN KEY (roll_no) REFERENCES students(roll_no) ON DELETE CASCADE
            );
            """
        )


def query_df(sql, params=()):
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def summary_df():
    df = query_df(
        """SELECT s.roll_no, s.name, s.class,
                  COUNT(a.status) AS total,
                  SUM(a.status = 'Present') AS present,
                  SUM(a.status = 'Late')    AS late,
                  SUM(a.status = 'Absent')  AS absent
           FROM students s LEFT JOIN attendance a USING (roll_no)
           GROUP BY s.roll_no ORDER BY s.roll_no"""
    ).fillna(0)
    for c in ("total", "present", "late", "absent"):
        df[c] = df[c].astype(int)
    # Late counts as attended
    pct = (df["present"] + df["late"]) / df["total"].where(df["total"] > 0) * 100
    df["percent"] = pct.fillna(0).round(1)
    return df


def valid_date(text):
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


# ---------- Small UI helpers ----------
def make_button(parent, text, command, color=PRIMARY, fg="white", padx=18, pady=8):
    btn = tk.Label(parent, text=text, bg=color, fg=fg, font=(FONT, 10, "bold"),
                   padx=padx, pady=pady, cursor="hand2")
    btn.bind("<Button-1>", lambda e: command())
    shade = {"enter": _shade(color, -18), "leave": color}
    btn.bind("<Enter>", lambda e: btn.config(bg=shade["enter"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=shade["leave"]))
    return btn


def _shade(hex_color, amount):
    h = hex_color.lstrip("#")
    r, g, b = (max(0, min(255, int(h[i:i + 2], 16) + amount)) for i in (0, 2, 4))
    return f"#{r:02x}{g:02x}{b:02x}"


def make_entry(parent, width=18):
    return tk.Entry(parent, width=width, font=(FONT, 11), relief="flat", bg="#FFFFFF",
                    fg=TEXT, insertbackground=TEXT, highlightthickness=1,
                    highlightbackground=BORDER, highlightcolor=PRIMARY)


def card_frame(parent, **kw):
    return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, **kw)


def page_header(parent, title, subtitle):
    box = tk.Frame(parent, bg=BG)
    tk.Label(box, text=title, bg=BG, fg=TEXT, font=(FONT, 20, "bold")).pack(anchor="w")
    tk.Label(box, text=subtitle, bg=BG, fg=MUTED, font=(FONT, 10)).pack(anchor="w")
    return box


def make_table(parent, columns, widths, height=12):
    """columns: list of (id, heading). Returns (frame, tree)."""
    frame = tk.Frame(parent, bg=CARD)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                        height=height, style="App.Treeview")
    for (cid, head), w in zip(columns, widths):
        tree.heading(cid, text=head)
        tree.column(cid, width=w, anchor="w")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    tree.tag_configure("odd", background="#FFFFFF")
    tree.tag_configure("even", background="#F8F9FD")
    tree.tag_configure("low", foreground=RED)
    tree.tag_configure("good", foreground=GREEN)
    return frame, tree


def fill_table(tree, rows, tag_fn=None):
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tags = ["even" if i % 2 else "odd"]
        if tag_fn:
            extra = tag_fn(row)
            if extra:
                tags.append(extra)
        tree.insert("", "end", values=row, tags=tags)


class StatusToggle(tk.Frame):
    """Segmented Present / Late / Absent control bound to a StringVar."""

    def __init__(self, parent, var):
        super().__init__(parent, bg=CARD)
        self.var = var
        self.labels = {}
        for status in ("Present", "Late", "Absent"):
            lb = tk.Label(self, text=status, font=(FONT, 9, "bold"), width=9, pady=5,
                          cursor="hand2", bd=0)
            lb.pack(side="left", padx=2)
            lb.bind("<Button-1>", lambda e, s=status: self.var.set(s))
            self.labels[status] = lb
        self.var.trace_add("write", lambda *a: self.refresh())
        self.refresh()

    def refresh(self):
        current = self.var.get()
        for status, lb in self.labels.items():
            if status == current:
                lb.config(bg=STATUS_COLORS[status], fg="white")
            else:
                lb.config(bg="#EEF0F7", fg=MUTED)


# ---------- Pages ----------
class DashboardPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        page_header(self, "Dashboard", "Today's overview at a glance").pack(anchor="w")

        self.cards_row = tk.Frame(self, bg=BG)
        self.cards_row.pack(fill="x", pady=(18, 10))
        self.stat_labels = {}
        for key, title, color in [
            ("students", "Total Students", PRIMARY),
            ("present", "Present Today", GREEN),
            ("late", "Late Today", AMBER),
            ("absent", "Absent Today", RED),
            ("overall", "Overall Attendance", "#8B5CF6"),
        ]:
            c = card_frame(self.cards_row)
            c.pack(side="left", expand=True, fill="x", padx=(0, 12))
            tk.Frame(c, bg=color, height=4).pack(fill="x")
            tk.Label(c, text=title, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=14, pady=(10, 0))
            lb = tk.Label(c, text="0", bg=CARD, fg=TEXT, font=(FONT, 24, "bold"))
            lb.pack(anchor="w", padx=14, pady=(0, 12))
            self.stat_labels[key] = lb

        tk.Label(self, text="Needs attention (below 75%)", bg=BG, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(anchor="w", pady=(14, 6))
        wrap = card_frame(self)
        wrap.pack(fill="both", expand=True)
        frame, self.tree = make_table(
            wrap, [("roll", "Roll No"), ("name", "Name"), ("cls", "Class"), ("pct", "Attendance %")],
            [120, 280, 120, 140], height=8)
        frame.pack(fill="both", expand=True)

    def refresh(self):
        today = date.today().isoformat()
        df = summary_df()
        day = query_df("SELECT status, COUNT(*) AS n FROM attendance WHERE date = ? GROUP BY status",
                       (today,))
        counts = dict(zip(day["status"], day["n"]))
        self.stat_labels["students"].config(text=str(len(df)))
        self.stat_labels["present"].config(text=str(counts.get("Present", 0)))
        self.stat_labels["late"].config(text=str(counts.get("Late", 0)))
        self.stat_labels["absent"].config(text=str(counts.get("Absent", 0)))
        marked = df[df["total"] > 0]
        overall = marked["percent"].mean() if not marked.empty else 0
        self.stat_labels["overall"].config(text=f"{overall:.0f}%")
        low = marked[marked["percent"] < 75]
        fill_table(self.tree,
                   [(r.roll_no, r.name, r["class"], f"{r.percent}%") for _, r in low.iterrows()],
                   lambda row: "low")


class StudentsPage(tk.Frame):
    def __init__(self, parent, on_change):
        super().__init__(parent, bg=BG)
        self.on_change = on_change
        page_header(self, "Students", "Add, search and remove students").pack(anchor="w")

        form = card_frame(self)
        form.pack(fill="x", pady=(18, 12))
        inner = tk.Frame(form, bg=CARD)
        inner.pack(fill="x", padx=16, pady=14)
        self.roll = self._field(inner, 0, "Roll No", 12)
        self.name = self._field(inner, 1, "Full Name", 26)
        self.cls = self._field(inner, 2, "Class", 12)
        make_button(inner, "+ Add Student", self.add).grid(row=0, column=3, sticky="s")

        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        tk.Label(bar, text="Search:", bg=BG, fg=MUTED, font=(FONT, 10)).pack(side="left")
        self.search = make_entry(bar, 30)
        self.search.pack(side="left", padx=8, ipady=4)
        self.search.bind("<KeyRelease>", lambda e: self.refresh())
        make_button(bar, "Delete Selected", self.delete, color=RED).pack(side="right")

        wrap = card_frame(self)
        wrap.pack(fill="both", expand=True)
        frame, self.tree = make_table(
            wrap, [("roll", "Roll No"), ("name", "Name"), ("cls", "Class")], [140, 340, 140], height=12)
        frame.pack(fill="both", expand=True)

    @staticmethod
    def _field(parent, col, label, width):
        box = tk.Frame(parent, bg=CARD)
        box.grid(row=0, column=col, padx=(0, 14))
        tk.Label(box, text=label, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        entry = make_entry(box, width)
        entry.pack(ipady=5)
        return entry

    def add(self):
        roll, name, cls = self.roll.get().strip(), self.name.get().strip(), self.cls.get().strip()
        if not roll or not name:
            messagebox.showwarning("Missing info", "Roll number and name are required.")
            return
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO students VALUES (?, ?, ?)", (roll, name, cls))
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", f"Roll number {roll} already exists.")
            return
        for e in (self.roll, self.name, self.cls):
            e.delete(0, "end")
        self.roll.focus_set()
        self.on_change()

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select a student", "Click a student in the table first.")
            return
        roll, name = self.tree.item(sel[0])["values"][:2]
        if messagebox.askyesno("Confirm", f"Delete {name} and all their attendance records?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM students WHERE roll_no = ?", (str(roll),))
            self.on_change()

    def refresh(self):
        term = f"%{self.search.get().strip()}%"
        df = query_df("""SELECT roll_no, name, class FROM students
                         WHERE roll_no LIKE ? OR name LIKE ? OR class LIKE ? ORDER BY roll_no""",
                      (term, term, term))
        fill_table(self.tree, list(df.itertuples(index=False, name=None)))


class MarkPage(tk.Frame):
    def __init__(self, parent, on_change):
        super().__init__(parent, bg=BG)
        self.on_change = on_change
        self.rows = []  # (roll_no, StringVar)
        page_header(self, "Mark Attendance", "Pick a date and class, then tap a status for each student").pack(anchor="w")

        ctrl = card_frame(self)
        ctrl.pack(fill="x", pady=(18, 12))
        inner = tk.Frame(ctrl, bg=CARD)
        inner.pack(fill="x", padx=16, pady=12)
        tk.Label(inner, text="Date", bg=CARD, fg=MUTED, font=(FONT, 9)).grid(row=0, column=0, sticky="w")
        tk.Label(inner, text="Class", bg=CARD, fg=MUTED, font=(FONT, 9)).grid(row=0, column=1, sticky="w", padx=(14, 0))
        self.date_entry = make_entry(inner, 14)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(row=1, column=0, ipady=5)
        self.class_box = ttk.Combobox(inner, state="readonly", width=14, font=(FONT, 11))
        self.class_box.grid(row=1, column=1, padx=(14, 0), ipady=3)
        make_button(inner, "Load", self.load, pady=7).grid(row=1, column=2, padx=14)
        make_button(inner, "All Present", self.all_present, color=GREEN, pady=7).grid(row=1, column=3)

        wrap = card_frame(self)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, bg=CARD, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=CARD)
        self.win = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._wheel)

        foot = tk.Frame(self, bg=BG)
        foot.pack(fill="x", pady=(10, 0))
        self.info = tk.Label(foot, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self.info.pack(side="left")
        make_button(foot, "Save Attendance", self.save, padx=24, pady=10).pack(side="right")

    def _wheel(self, event):
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def refresh(self):
        classes = query_df("SELECT DISTINCT class FROM students WHERE class != '' ORDER BY class")["class"].tolist()
        self.class_box["values"] = ["All"] + classes
        if self.class_box.get() not in self.class_box["values"]:
            self.class_box.set("All")
        self.load()

    def load(self):
        day = valid_date(self.date_entry.get())
        if not day:
            messagebox.showerror("Invalid date", "Use the format YYYY-MM-DD.")
            return
        cls = self.class_box.get()
        sql = "SELECT roll_no, name FROM students"
        params = ()
        if cls and cls != "All":
            sql += " WHERE class = ?"
            params = (cls,)
        students = query_df(sql + " ORDER BY roll_no", params)
        existing = query_df("SELECT roll_no, status FROM attendance WHERE date = ?", (day,))
        saved = dict(zip(existing["roll_no"], existing["status"]))

        for w in self.list_frame.winfo_children():
            w.destroy()
        self.rows = []
        if students.empty:
            tk.Label(self.list_frame, text="No students found. Add some on the Students page.",
                     bg=CARD, fg=MUTED, font=(FONT, 11), pady=30).pack()
        for i, s in students.iterrows():
            row = tk.Frame(self.list_frame, bg=CARD if i % 2 == 0 else "#F8F9FD")
            row.pack(fill="x")
            tk.Label(row, text=s.roll_no, bg=row["bg"], fg=MUTED, font=(FONT, 10), width=10,
                     anchor="w").pack(side="left", padx=(16, 0), pady=8)
            tk.Label(row, text=s["name"], bg=row["bg"], fg=TEXT, font=(FONT, 11, "bold"),
                     anchor="w").pack(side="left", padx=10)
            var = tk.StringVar(value=saved.get(s.roll_no, "Present"))
            tog = StatusToggle(row, var)
            tog.config(bg=row["bg"])
            tog.pack(side="right", padx=16)
            self.rows.append((s.roll_no, var))
        edited = "already marked, editing" if saved else "not marked yet"
        self.info.config(text=f"{len(self.rows)} students  -  {day} ({edited})")

    def all_present(self):
        for _, var in self.rows:
            var.set("Present")

    def save(self):
        day = valid_date(self.date_entry.get())
        if not day or not self.rows:
            messagebox.showwarning("Nothing to save", "Load a valid date and class with students first.")
            return
        with get_conn() as conn:
            conn.executemany("INSERT OR REPLACE INTO attendance VALUES (?, ?, ?)",
                             [(r, day, v.get()) for r, v in self.rows])
        messagebox.showinfo("Saved", f"Attendance saved for {len(self.rows)} students on {day}.")
        self.on_change()


class ReportsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x")
        page_header(head, "Reports", "Attendance percentage per student (Late counts as attended)").pack(side="left")
        make_button(head, "Export Log", lambda: self.export("log"), color="#5B6489").pack(side="right")
        make_button(head, "Export Summary", lambda: self.export("summary"), color=GREEN).pack(side="right", padx=8)

        wrap = card_frame(self)
        wrap.pack(fill="both", expand=True, pady=(18, 0))
        frame, self.tree = make_table(
            wrap,
            [("roll", "Roll No"), ("name", "Name"), ("cls", "Class"), ("total", "Days"),
             ("present", "Present"), ("late", "Late"), ("absent", "Absent"), ("pct", "Attendance %")],
            [90, 220, 90, 70, 80, 70, 80, 120], height=16)
        frame.pack(fill="both", expand=True)

    def refresh(self):
        df = summary_df()
        rows = [(r.roll_no, r.name, r["class"], r.total, r.present, r.late, r.absent, f"{r.percent}%")
                for _, r in df.iterrows()]

        def tag(row):
            if row[3] == 0:
                return None
            pct = float(row[7].rstrip("%"))
            return "low" if pct < 75 else ("good" if pct >= 90 else None)

        fill_table(self.tree, rows, tag)

    def export(self, kind):
        stamp = datetime.now().strftime("%Y%m%d")
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
            initialfile=f"attendance_{kind}_{stamp}.csv")
        if not path:
            return
        if kind == "summary":
            df = summary_df()
        else:
            df = query_df("""SELECT a.date, s.roll_no, s.name, s.class, a.status
                             FROM attendance a JOIN students s USING (roll_no)
                             ORDER BY a.date, s.roll_no""")
        df.to_csv(path, index=False)
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


# ---------- Main window ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Attendance System")
        self.geometry("1150x700")
        self.minsize(980, 600)
        self.configure(bg=BG)
        self._style()

        side = tk.Frame(self, bg=SIDEBAR, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="Attendance", bg=SIDEBAR, fg="white", font=(FONT, 18, "bold")).pack(anchor="w", padx=22, pady=(28, 0))
        tk.Label(side, text="Student tracker", bg=SIDEBAR, fg="#9AA3C7", font=(FONT, 9)).pack(anchor="w", padx=22, pady=(0, 28))

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True, padx=28, pady=24)

        self.pages = {
            "Dashboard": DashboardPage(self.content),
            "Students": StudentsPage(self.content, self.refresh_all),
            "Mark Attendance": MarkPage(self.content, self.refresh_all),
            "Reports": ReportsPage(self.content),
        }
        self.nav = {}
        for name in self.pages:
            lb = tk.Label(side, text=f"   {name}", bg=SIDEBAR, fg="#C9CFEA", font=(FONT, 11),
                          anchor="w", pady=11, cursor="hand2")
            lb.pack(fill="x", padx=12, pady=2)
            lb.bind("<Button-1>", lambda e, n=name: self.show(n))
            lb.bind("<Enter>", lambda e, l=lb, n=name: self.current != n and l.config(bg=SIDEBAR_HOVER))
            lb.bind("<Leave>", lambda e, l=lb, n=name: self.current != n and l.config(bg=SIDEBAR))
            self.nav[name] = lb
        tk.Label(side, text=date.today().strftime("%A, %d %b %Y"), bg=SIDEBAR, fg="#9AA3C7",
                 font=(FONT, 9)).pack(side="bottom", pady=18)

        self.current = None
        self.show("Dashboard")

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("App.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground=TEXT,
                    rowheight=34, borderwidth=0, font=(FONT, 10))
        s.configure("App.Treeview.Heading", background="#EEF1F9", foreground=MUTED,
                    font=(FONT, 9, "bold"), relief="flat", padding=(8, 8))
        s.map("App.Treeview", background=[("selected", "#DDE4FF")], foreground=[("selected", TEXT)])
        s.map("App.Treeview.Heading", background=[("active", "#E3E8F6")])

    def show(self, name):
        for n, page in self.pages.items():
            page.pack_forget()
            self.nav[n].config(bg=SIDEBAR, fg="#C9CFEA")
        self.current = name
        self.nav[name].config(bg=SIDEBAR_ACTIVE, fg="white")
        self.pages[name].pack(fill="both", expand=True)
        self.pages[name].refresh()

    def refresh_all(self):
        self.pages[self.current].refresh()


if __name__ == "__main__":
    init_db()
    App().mainloop()
