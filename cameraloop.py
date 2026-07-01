import time

import cv2
import mediapipe as mp

from gameconfig import (
    answer_hold,
    camera_height,
    camera_index,
    camera_width,
    input_confirm,
    model_path,
    pose_index,
)
from gamelogic import finalize_answer, prepare_next_round
from posedetector import detect_pose
from gamestate import publish_state, reset_runtime, set_event


def draw_overlay(frame, runtime: dict, gesture: str, confirm_elapsed: float) -> None:
    """Draw simple debug information on the camera window."""
    def text(line, y, color=(255, 255, 255), scale=0.65):
        cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2)

    text(f"Detected: {gesture}", 40, (0, 255, 0), 0.72)
    text(f"Confirmed: {runtime['confirmed_pose']}", 72, (255, 220, 0), 0.72)
    text(f"Confirm: {min(confirm_elapsed, input_confirm):.1f}/{input_confirm:.0f}s", 104, (0, 255, 255), 0.66)
    text(f"Score: {runtime['score']}  Round: {runtime['round_index']}/{runtime['rounds_total']}", 136, (255, 255, 255), 0.62)

    if runtime["selected_index"] is not None and runtime["choices"]:
        selected = runtime["choices"][runtime["selected_index"]]
        text(f"Selected: {selected['jp']}", 168, (255, 255, 255), 0.60)
        text(f"Hold: {runtime['hold_progress']:.1f}/{answer_hold:.0f}s", 198, (255, 200, 0), 0.60)

    if runtime["needs_release_for_next"]:
        text("Hold RELEASE for next round", 232, (255, 105, 180), 0.62)
    if not runtime["session_started"]:
        text("Hold RELEASE to start", 232, (255, 105, 180), 0.72)
    if runtime["session_completed"]:
        text("SESSION COMPLETE - Press R to restart", 232, (255, 105, 180), 0.72)


def camera_loop(session_questions: list) -> None:
    """Main loop: camera input -> pose -> game state."""
    runtime = reset_runtime()
    publish_state(runtime, "Hold RELEASE to start")

    cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
    time.sleep(1.0)
    if not cap.isOpened():
        raise RuntimeError("Camera failed to open")

    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.02)
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

            gesture = "NONE"
            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                gesture = detect_pose(result.pose_landmarks[0])

            now = time.time()
            confirm_elapsed = 0.0
            message = ""

            if runtime["session_completed"]:
                publish_state(runtime, "Session complete")
                draw_overlay(frame, runtime, gesture, confirm_elapsed)
                cv2.imshow("Tango Challenge Pose Camera", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("r"):
                    runtime = reset_runtime()
                    publish_state(runtime, "Hold RELEASE to start")
                elif key == 27:
                    break
                continue

            if gesture == "RELEASE":
                if runtime["candidate"] != "RELEASE":
                    runtime["candidate"] = "RELEASE"
                    runtime["candidate_start"] = now
                    runtime["confirmed_pose"] = "NONE"
                    runtime["active_pose_start"] = None
                else:
                    confirm_elapsed = now - runtime["candidate_start"] if runtime["candidate_start"] else 0.0
                    if confirm_elapsed >= input_confirm:
                        runtime["confirmed_pose"] = "RELEASE"
                        if not runtime["session_started"]:
                            runtime["session_started"] = True
                            prepare_next_round(runtime, session_questions)
                            set_event(runtime, "start", runtime["round_index"])
                            message = "Game started"
                        elif runtime["needs_release_for_next"]:
                            prepare_next_round(runtime, session_questions)
                            message = "Cards randomized"

            elif gesture in pose_index and runtime["session_started"] and not runtime["needs_release_for_next"]:
                if runtime["candidate"] != gesture:
                    runtime["candidate"] = gesture
                    runtime["candidate_start"] = now
                    runtime["confirmed_pose"] = "NONE"
                    runtime["active_pose_start"] = None
                    runtime["selected_index"] = None
                    runtime["hold_progress"] = 0.0
                else:
                    confirm_elapsed = now - runtime["candidate_start"] if runtime["candidate_start"] else 0.0
                    if confirm_elapsed >= input_confirm:
                        selected_idx = pose_index[gesture]
                        runtime["selected_index"] = selected_idx

                        if runtime["confirmed_pose"] != gesture:
                            runtime["confirmed_pose"] = gesture
                            runtime["active_pose_start"] = now
                        else:
                            dt = now - runtime["active_pose_start"] if runtime["active_pose_start"] else 0.0
                            runtime["active_pose_start"] = now
                            runtime["hold_progress"] += dt
                            if runtime["hold_progress"] >= answer_hold:
                                runtime["hold_progress"] = answer_hold
                                finalize_answer(runtime)
                                message = "Correct! +10 points" if runtime["correct"] else "Wrong! +5 points"

            else:
                runtime["candidate"] = "NONE"
                runtime["candidate_start"] = None
                if not runtime["needs_release_for_next"]:
                    runtime["confirmed_pose"] = "NONE"
                    runtime["active_pose_start"] = None
                    runtime["selected_index"] = None
                    runtime["hold_progress"] = 0.0

            publish_state(runtime, message)
            draw_overlay(frame, runtime, gesture, confirm_elapsed)

            cv2.imshow("Tango Challenge Pose Camera", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("r"):
                runtime = reset_runtime()
                publish_state(runtime, "Hold RELEASE to start")
            elif key == 27:
                break
    finally:
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()
