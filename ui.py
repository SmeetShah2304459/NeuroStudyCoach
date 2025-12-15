import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
from analytics import productivity_by_hour, subject_pareto, forecast_hours_needed, best_focus_window

def _df_to_tree(tree: ttk.Treeview, df: pd.DataFrame):
    tree.delete(*tree.get_children())
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=120)
    for _, row in df.iterrows():
        tree.insert("", "end", values=[row.get(c, "") for c in df.columns])

class DashboardTab(ttk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        top = ttk.Frame(self); top.pack(fill="x", padx=12, pady=12)
        self.kpi_hours = ttk.Label(top, text="Hours Needed: --", font=("Segoe UI", 12, "bold"))
        self.kpi_best = ttk.Label(top, text="Best Focus Window: --", font=("Segoe UI", 12, "bold"))
        self.kpi_tasks = ttk.Label(top, text="Open Tasks: --", font=("Segoe UI", 12, "bold"))
        self.kpi_hours.pack(side="left", padx=10)
        self.kpi_best.pack(side="left", padx=10)
        self.kpi_tasks.pack(side="left", padx=10)

        mid = ttk.Frame(self); mid.pack(fill="both", expand=True, padx=12, pady=6)
        # Productivity by hour table
        left = ttk.Labelframe(mid, text="Productivity by Hour (mood/energy & minutes)")
        left.pack(side="left", fill="both", expand=True, padx=(0,6))
        self.tree_prod = ttk.Treeview(left, height=12)
        self.tree_prod.pack(fill="both", expand=True, padx=6, pady=6)

        # Subject Pareto
        right = ttk.Labelframe(mid, text="Subject Pareto (minutes vs open tasks)")
        right.pack(side="left", fill="both", expand=True, padx=(6,0))
        self.tree_pareto = ttk.Treeview(right, height=12)
        self.tree_pareto.pack(fill="both", expand=True, padx=6, pady=6)

        btn = ttk.Button(self, text="Refresh", command=self.refresh)
        btn.pack(pady=8)

    def refresh(self):
        tasks = self.controller.list_tasks()
        sessions = self.controller.list_sessions()

        prod = productivity_by_hour(sessions)
        _df_to_tree(self.tree_prod, prod)

        pareto = subject_pareto(tasks, sessions)
        _df_to_tree(self.tree_pareto, pareto)

        hours = forecast_hours_needed(tasks, sessions)
        best = best_focus_window(prod)
        open_tasks = len(tasks[tasks["status"].isin(["Todo","In Progress"])])
        self.kpi_hours.config(text=f"Hours Needed: {hours}")
        self.kpi_best.config(text=f"Best Focus Window: {best}")
        self.kpi_tasks.config(text=f"Open Tasks: {open_tasks}")

class SessionsTab(ttk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        form = ttk.Labelframe(self, text="Log Study Session")
        form.pack(fill="x", padx=12, pady=12)
        self.vars = {k: tk.StringVar() for k in ["date","start","end","duration","subject","mood","energy","notes"]}
        grid = [
            ("Date (YYYY-MM-DD)", "date"),
            ("Start (HH:MM)", "start"),
            ("End (HH:MM)", "end"),
            ("Duration (min)", "duration"),
            ("Subject", "subject"),
            ("Mood (1-10)", "mood"),
            ("Energy (1-10)", "energy"),
            ("Notes", "notes"),
        ]
        for i,(lbl,key) in enumerate(grid):
            ttk.Label(form, text=lbl).grid(row=i//2, column=(i%2)*2, padx=6, pady=6, sticky="e")
            ttk.Entry(form, textvariable=self.vars[key], width=24).grid(row=i//2, column=(i%2)*2+1, padx=6, pady=6, sticky="w")
        ttk.Button(form, text="Add Session", command=self._add).grid(row=4, column=0, columnspan=2, padx=6, pady=10, sticky="ew")
        ttk.Button(form, text="Delete Selected", command=self._delete).grid(row=4, column=2, columnspan=2, padx=6, pady=10, sticky="ew")

        table = ttk.Labelframe(self, text="Sessions")
        table.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.tree = ttk.Treeview(table)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.refresh()

    def _add(self):
        try:
            d = self.vars["date"].get().strip() or datetime.now().date().isoformat()
            st = self.vars["start"].get().strip() or "09:00"
            et = self.vars["end"].get().strip() or "09:25"
            du = int(self.vars["duration"].get().strip() or "25")
            subj = self.vars["subject"].get().strip() or "General"
            mood = int(self.vars["mood"].get().strip() or "7")
            energy = int(self.vars["energy"].get().strip() or "7")
            notes = self.vars["notes"].get().strip()
            self.controller.add_session(d, st, et, du, subj, mood, energy, notes)
            self.event_generate("<<DataChanged>>", when="tail")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.refresh()

    def _delete(self):
        try:
            item = self.tree.selection()[0]
            vals = self.tree.item(item)["values"]
            row_id = int(vals[0])
            self.controller.delete_session(row_id)
            self.event_generate("<<DataChanged>>", when="tail")
            self.refresh()
        except IndexError:
            messagebox.showinfo("Info", "Select a row to delete.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        df = self.controller.list_sessions()
        if df.empty:
            df = pd.DataFrame(columns=["id","date","start_time","end_time","duration_min","subject","mood","energy","notes"])
        _df_to_tree(self.tree, df)

class TasksTab(ttk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        form = ttk.Labelframe(self, text="Add Task")
        form.pack(fill="x", padx=12, pady=12)
        self.vars = {k: tk.StringVar() for k in ["title","subject","deadline","priority","estimated_min","status"]}
        grid = [
            ("Title", "title"),
            ("Subject", "subject"),
            ("Deadline (YYYY-MM-DD)", "deadline"),
            ("Priority (Low/Medium/High)", "priority"),
            ("Estimated Minutes", "estimated_min"),
            ("Status (Todo/In Progress/Done)", "status"),
        ]
        for i,(lbl,key) in enumerate(grid):
            ttk.Label(form, text=lbl).grid(row=i//2, column=(i%2)*2, padx=6, pady=6, sticky="e")
            ttk.Entry(form, textvariable=self.vars[key], width=28).grid(row=i//2, column=(i%2)*2+1, padx=6, pady=6, sticky="w")
        ttk.Button(form, text="Add Task", command=self._add).grid(row=3, column=0, columnspan=2, padx=6, pady=10, sticky="ew")

        actions = ttk.Frame(form); actions.grid(row=3, column=2, columnspan=2, sticky="ew", padx=6)
        ttk.Button(actions, text="Mark Done", command=lambda: self._update_status("Done")).pack(side="left", padx=4)
        ttk.Button(actions, text="In Progress", command=lambda: self._update_status("In Progress")).pack(side="left", padx=4)
        ttk.Button(actions, text="Delete", command=self._delete).pack(side="left", padx=4)

        table = ttk.Labelframe(self, text="Tasks")
        table.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.tree = ttk.Treeview(table)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.refresh()

    def _add(self):
        try:
            vals = {k: v.get().strip() for k,v in self.vars.items()}
            if not vals["title"]:
                raise ValueError("Title is required.")
            vals.setdefault("priority", "Medium")
            vals.setdefault("status", "Todo")
            self.controller.add_task(**vals)
            self.event_generate("<<DataChanged>>", when="tail")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _selected_row_id(self):
        item = self.tree.selection()
        if not item:
            raise IndexError("Select a row first.")
        vals = self.tree.item(item[0])["values"]
        return int(vals[0])

    def _update_status(self, status):
        try:
            rid = self._selected_row_id()
            self.controller.update_task_status(rid, status)
            self.event_generate("<<DataChanged>>", when="tail")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        try:
            rid = self._selected_row_id()
            self.controller.delete_task(rid)
            self.event_generate("<<DataChanged>>", when="tail")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        df = self.controller.list_tasks()
        if df.empty:
            df = pd.DataFrame(columns=["id","title","subject","deadline","priority","estimated_min","status"])
        _df_to_tree(self.tree, df)

class AnalyticsTab(ttk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        top = ttk.Frame(self); top.pack(fill="x", padx=12, pady=12)
        ttk.Button(top, text="Recompute Analytics", command=self.refresh).pack(side="left")

        self.box = ttk.Labelframe(self, text="Insights")
        self.box.pack(fill="both", expand=True, padx=12, pady=(0,12))

        self.txt = tk.Text(self.box, height=18, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self):
        tasks = self.controller.list_tasks()
        sessions = self.controller.list_sessions()
        prod = productivity_by_hour(sessions)
        pareto = subject_pareto(tasks, sessions)
        hours = forecast_hours_needed(tasks, sessions)
        best = best_focus_window(prod)

        lines = []
        lines.append("🔥 Key Insights")
        lines.append("")
        lines.append(f"• Estimated hours needed to finish remaining tasks: {hours}")
        lines.append(f"• Best focus window (based on mood/energy): {best}")
        lines.append("")
        lines.append("📌 Productivity by Hour:")
        if prod.empty:
            lines.append("  - Not enough data yet.")
        else:
            for _,r in prod.iterrows():
                lines.append(f"  - {int(r['hour']):02d}:00 → avg mood {r['avg_mood']:.1f}, energy {r['avg_energy']:.1f}, total {int(r['total_min'])} min")
        lines.append("")
        lines.append("📌 Subject Pareto:")
        if pareto.empty:
            lines.append("  - Not enough data yet.")
        else:
            for _,r in pareto.iterrows():
                lines.append(f"  - {r['subject']}: {int(r['minutes_spent'])} min spent, {int(r['open_tasks'])} tasks open")

        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(lines))

class SettingsTab(ttk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.vars = {k: tk.StringVar() for k in ["pomodoro_min","short_break_min","long_break_min","long_break_every"]}

        box = ttk.Labelframe(self, text="Pomodoro Settings")
        box.pack(fill="x", padx=12, pady=12)

        grid = [
            ("Pomodoro (min)", "pomodoro_min"),
            ("Short Break (min)", "short_break_min"),
            ("Long Break (min)", "long_break_min"),
            ("Long Break Every (cycles)", "long_break_every"),
        ]
        for i,(lbl,key) in enumerate(grid):
            ttk.Label(box, text=lbl).grid(row=i, column=0, sticky="e", padx=6, pady=6)
            ttk.Entry(box, textvariable=self.vars[key], width=10).grid(row=i, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(self, text="Save", command=self._save).pack(pady=8)
        self.refresh()

    def refresh(self):
        data = self.controller.get_settings()
        for k in self.vars:
            self.vars[k].set(str(data.get(k, "")))

    def _save(self):
        try:
            data = {k:int(v.get()) for k,v in self.vars.items()}
            self.controller.save_settings(data)
            messagebox.showinfo("Saved", "Settings saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
