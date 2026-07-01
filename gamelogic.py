from gameconfig import answer_hold
from imagecache import build_card_item
from gamestate import set_event


def prepare_next_round(runtime: dict, session_questions: list) -> None:
    """Move to the next question and prepare its card image."""
    runtime["round_index"] += 1

    if runtime["round_index"] > runtime["rounds_total"]:
        runtime["session_completed"] = True
        runtime["target"] = None
        runtime["choices"] = []
        runtime["selected_index"] = None
        runtime["hold_progress"] = 0.0
        runtime["needs_release_for_next"] = False
        set_event(runtime, "session_complete", runtime["score"])
        return

    question = session_questions[runtime["round_index"] - 1]
    target = question["target"]
    choices = question["choices"]

    runtime["target"] = build_card_item(target)
    runtime["choices"] = [dict(item) for item in choices]
    runtime["selected_index"] = None
    runtime["hold_progress"] = 0.0
    runtime["correct"] = None
    runtime["needs_release_for_next"] = False
    runtime["confirmed_pose"] = "NONE"
    runtime["active_pose_start"] = None
    runtime["candidate"] = "NONE"
    runtime["candidate_start"] = None
    set_event(runtime, "new_round", runtime["round_index"])


def finalize_answer(runtime: dict) -> None:
    """Check the selected answer and update the score."""
    idx = runtime["selected_index"]
    if idx is None:
        return

    is_correct = runtime["choices"][idx]["jp"] == runtime["target"]["jp"]
    runtime["correct"] = is_correct
    if is_correct:
        runtime["score"] += 10
        set_event(runtime, "correct", runtime["score"])
    else:
        runtime["score"] += 5
        set_event(runtime, "wrong", runtime["score"])

    runtime["needs_release_for_next"] = True
    runtime["hold_progress"] = answer_hold
