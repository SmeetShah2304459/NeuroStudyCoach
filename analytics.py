import pandas as pd
import numpy as np
from datetime import datetime

def _parse_date(df, col="date"):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df

def productivity_by_hour(sessions: pd.DataFrame) -> pd.DataFrame:
    """Return average mood/energy and minutes by start hour."""
    if sessions.empty:
        return pd.DataFrame(columns=["hour","avg_mood","avg_energy","total_min"])
    df = sessions.copy()
    _parse_date(df, "date")
    # derive hour from start_time
    def hourify(x):
        try:
            return int(str(x).split(":")[0])
        except Exception:
            return None
    df["hour"] = df["start_time"].map(hourify)
    g = df.groupby("hour").agg(
        avg_mood=("mood","mean"),
        avg_energy=("energy","mean"),
        total_min=("duration_min","sum")
    ).reset_index().sort_values("hour")
    return g

def subject_pareto(tasks: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """Which subjects consume most time vs open tasks (80/20)."""
    s = sessions.copy()
    t = tasks.copy()
    if s.empty and t.empty:
        return pd.DataFrame(columns=["subject","minutes_spent","open_tasks"])
    s_minutes = s.groupby("subject")["duration_min"].sum().rename("minutes_spent")
    t_open = t[t["status"].isin(["Todo","In Progress"])].groupby("subject")["id"].count().rename("open_tasks")
    out = pd.concat([s_minutes, t_open], axis=1).fillna(0).reset_index()
    out = out.sort_values("minutes_spent", ascending=False)
    return out

def forecast_hours_needed(tasks: pd.DataFrame, sessions: pd.DataFrame) -> float:
    """Estimate hours needed to finish remaining tasks based on velocity."""
    remaining_min = tasks[tasks["status"].isin(["Todo","In Progress"])]["estimated_min"].sum()
    if remaining_min <= 0:
        return 0.0
    # Velocity: rolling average of last 7 days minutes from sessions
    if sessions.empty:
        return remaining_min / 60.0
    s = sessions.copy()
    s["date"] = pd.to_datetime(s["date"], errors="coerce")
    daily = s.groupby(s["date"].dt.date)["duration_min"].sum().reset_index()
    if daily.empty:
        return remaining_min / 60.0
    # Fit simple linear trend to infer tomorrow+ productivity
    x = np.arange(len(daily))
    y = daily["duration_min"].to_numpy()
    # Handle constant or tiny arrays
    if len(x) >= 2 and np.std(y) > 0:
        coeffs = np.polyfit(x, y, 1)
        # predicted next 7 days mins (non-negative)
        preds = np.clip(np.polyval(coeffs, np.arange(len(daily), len(daily)+7)), 0, None)
        weekly_capacity = preds.sum()
    else:
        weekly_capacity = y.mean() * 7.0
    if weekly_capacity <= 1e-6:
        return remaining_min / 60.0
    weeks_needed = remaining_min / weekly_capacity
    return round(weeks_needed * 7 * 24, 2)  # convert weeks to hours

def best_focus_window(prod_hour_df: pd.DataFrame) -> str:
    """Return a human-friendly best hour-of-day window based on mood+energy."""
    if prod_hour_df.empty:
        return "No data yet — run a few sessions."
    df = prod_hour_df.copy()
    df["score"] = df["avg_mood"].fillna(0)*0.6 + df["avg_energy"].fillna(0)*0.4
    best = df.sort_values(["score","total_min"], ascending=False).head(1)
    hr = int(best["hour"].iloc[0])
    return f"{hr:02d}:00–{hr+1:02d}:00"
