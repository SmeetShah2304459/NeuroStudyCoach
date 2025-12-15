from storage import Storage
import pandas as pd
from datetime import datetime, timedelta

class AppController:
    def __init__(self, storage: Storage):
        self.storage = storage

    # --- Sessions ---
    def list_sessions(self) -> pd.DataFrame:
        return self.storage.load_sessions()

    def add_session(self, date, start_time, end_time, duration_min, subject, mood, energy, notes):
        df = self.storage.load_sessions()
        new = {
            "id": self.storage.next_session_id(),
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "duration_min": int(duration_min or 0),
            "subject": subject,
            "mood": int(mood or 0),
            "energy": int(energy or 0),
            "notes": notes or ""
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        self.storage.save_sessions(df)
        return new

    def delete_session(self, row_id: int):
        df = self.storage.load_sessions()
        df = df[df["id"] != row_id]
        self.storage.save_sessions(df)

    # --- Tasks ---
    def list_tasks(self) -> pd.DataFrame:
        return self.storage.load_tasks()

    def add_task(self, title, subject, deadline, priority, estimated_min, status):
        df = self.storage.load_tasks()
        new = {
            "id": self.storage.next_task_id(),
            "title": title, "subject": subject, "deadline": deadline,
            "priority": priority, "estimated_min": int(estimated_min or 0),
            "status": status
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        self.storage.save_tasks(df)
        return new

    def update_task_status(self, row_id: int, status: str):
        df = self.storage.load_tasks()
        df.loc[df["id"] == row_id, "status"] = status
        self.storage.save_tasks(df)

    def delete_task(self, row_id: int):
        df = self.storage.load_tasks()
        df = df[df["id"] != row_id]
        self.storage.save_tasks(df)

    # --- Settings ---
    def get_settings(self) -> dict:
        return self.storage.load_settings()

    def save_settings(self, data: dict):
        self.storage.save_settings(data)
