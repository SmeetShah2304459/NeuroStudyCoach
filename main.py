"""
NeuroStudy Coach — Adaptive Study Planner & Focus Analytics
Tkinter + Pandas + NumPy. Pure Python files only.
Run: python main.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from storage import Storage
from controllers import AppController
from ui import DashboardTab, SessionsTab, TasksTab, AnalyticsTab, SettingsTab

APP_TITLE = "NeuroStudy Coach — Adaptive Study Planner & Focus Analytics"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x720")
        self.minsize(980, 650)
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Shared services
        self.storage = Storage(base_dir="data")
        self.controller = AppController(self.storage)

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        # Tabs
        self.dashboard_tab = DashboardTab(self.nb, self.controller)
        self.sessions_tab  = SessionsTab(self.nb, self.controller)
        self.tasks_tab     = TasksTab(self.nb, self.controller)
        self.analytics_tab = AnalyticsTab(self.nb, self.controller)
        self.settings_tab  = SettingsTab(self.nb, self.controller)

        self.nb.add(self.dashboard_tab, text="📊 Dashboard")
        self.nb.add(self.sessions_tab,  text="⏱️ Sessions")
        self.nb.add(self.tasks_tab,     text="📝 Tasks")
        self.nb.add(self.analytics_tab, text="📈 Analytics")
        self.nb.add(self.settings_tab,  text="⚙️ Settings")

        self.bind("<<DataChanged>>", self._on_data_changed)
        self.after(300, self.dashboard_tab.refresh)

    def _on_data_changed(self, _evt=None):
        # Refresh everybody lightly
        self.dashboard_tab.refresh()
        self.tasks_tab.refresh()
        self.sessions_tab.refresh()
        self.analytics_tab.refresh()

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    app = App()
    app.mainloop()
