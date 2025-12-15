import os
import pandas as pd
from datetime import datetime
from typing import Optional

class Storage:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.paths = {
            "sessions": os.path.join(self.base_dir, "sessions.csv"),
            "tasks": os.path.join(self.base_dir, "tasks.csv"),
            "settings": os.path.join(self.base_dir, "settings.json"),
        }
        self._bootstrap()

    def _bootstrap(self):
        # Create sample files if missing
        if not os.path.exists(self.paths["sessions"]):
            df = pd.DataFrame([
                {"id": 1, "date": datetime.now().date().isoformat(), "start_time": "09:00", "end_time": "09:25",
                 "duration_min": 25, "subject": "Math", "mood": 7, "energy": 6, "notes": "Good warm-up."},
                {"id": 2, "date": datetime.now().date().isoformat(), "start_time": "10:00", "end_time": "10:50",
                 "duration_min": 50, "subject": "Python", "mood": 8, "energy": 7, "notes": "Flow state!"},
            ])
            df.to_csv(self.paths["sessions"], index=False)
        if not os.path.exists(self.paths["tasks"]):
            df = pd.DataFrame([
                {"id": 1, "title": "Revise Calculus Ch.3", "subject": "Math", "deadline": "", "priority": "High", "estimated_min": 60, "status": "Todo"},
                {"id": 2, "title": "Project: Tkinter UI", "subject": "Python", "deadline": "", "priority": "Medium", "estimated_min": 120, "status": "In Progress"},
            ])
            df.to_csv(self.paths["tasks"], index=False)
        if not os.path.exists(self.paths["settings"]):
            import json
            with open(self.paths["settings"], "w", encoding="utf-8") as f:
                json.dump({"pomodoro_min": 25, "short_break_min": 5, "long_break_min": 15, "long_break_every": 4}, f)

    # --- Sessions ---
    def load_sessions(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.paths["sessions"])
        except Exception:
            return pd.DataFrame(columns=["id","date","start_time","end_time","duration_min","subject","mood","energy","notes"])

    def save_sessions(self, df: pd.DataFrame):
        df.to_csv(self.paths["sessions"], index=False)

    def next_session_id(self) -> int:
        df = self.load_sessions()
        return (df["id"].max() if not df.empty else 0) + 1

    # --- Tasks ---
    def load_tasks(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.paths["tasks"])
        except Exception:
            return pd.DataFrame(columns=["id","title","subject","deadline","priority","estimated_min","status"])

    def save_tasks(self, df: pd.DataFrame):
        df.to_csv(self.paths["tasks"], index=False)

    def next_task_id(self) -> int:
        df = self.load_tasks()
        return (df["id"].max() if not df.empty else 0) + 1

    # --- Settings ---
    def load_settings(self) -> dict:
        import json
        try:
            with open(self.paths["settings"], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"pomodoro_min": 25, "short_break_min": 5, "long_break_min": 15, "long_break_every": 4}

    def save_settings(self, data: dict):
        import json
        with open(self.paths["settings"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
