import threading
from gameconfig import round_session, cloudflare

default_state = {
    "session_started": False,
    "session_completed": False,
    "score": 0,
    "round_index": 0,
    "rounds_total": round_session,
    "message": "Hold RELEASE to start",
    "target": None,
    "choices": [],
    "selected_index": None,
    "confirmed_pose": "NONE",
    "hold_progress": 0.0,
    "event_id": 0,
    "event_type": "",
    "correct": None,
    "needs_release_for_next": False,
    "ai_enabled": cloudflare,
}

latest_state = dict(default_state)
state_lock = threading.Lock()
clients_lock = threading.Lock()
connected_clients = set()


def set_event(runtime: dict, event_type: str = "", event_value=None) -> None:
    runtime["event_id"] += 1
    runtime["event_type"] = event_type
    runtime["event_value"] = event_value


def reset_runtime() -> dict:
    return {
        "session_started": False,
        "session_completed": False,
        "score": 0,
        "round_index": 0,
        "rounds_total": round_session,
        "event_id": 0,
        "event_type": "",
        "candidate": "NONE",
        "candidate_start": None,
        "confirmed_pose": "NONE",
        "active_pose_start": None,
        "target": None,
        "choices": [],
        "selected_index": None,
        "hold_progress": 0.0,
        "correct": None,
        "needs_release_for_next": False,
    }


def publish_state(runtime: dict, message: str = "") -> None:
    """Update the state that will be sent to the browser."""
    with state_lock:
        latest_state.update({
            "session_started": runtime["session_started"],
            "session_completed": runtime["session_completed"],
            "score": runtime["score"],
            "round_index": runtime["round_index"],
            "rounds_total": runtime["rounds_total"],
            "message": message,
            "target": runtime.get("target"),
            "choices": runtime.get("choices", []),
            "selected_index": runtime.get("selected_index"),
            "confirmed_pose": runtime.get("confirmed_pose", "NONE"),
            "hold_progress": runtime.get("hold_progress", 0.0),
            "event_id": runtime.get("event_id", 0),
            "event_type": runtime.get("event_type", ""),
            "correct": runtime.get("correct"),
            "needs_release_for_next": runtime.get("needs_release_for_next", False),
            "ai_enabled": cloudflare,
        })
