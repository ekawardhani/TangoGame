import threading

from cardgenerator import generate_ai_session
from cameraloop import camera_loop
from gameconfig import game_html, http_port
from server import run_http_server, run_ws_server


def main() -> None:
    session_questions = generate_ai_session()

    threading.Thread(target=run_http_server, daemon=True).start()
    threading.Thread(target=run_ws_server, daemon=True).start()

    print("Open this in your browser:")
    print(f"http://127.0.0.1:{http_port}/{game_html}")
    print("AI content mode: ON")

    camera_loop(session_questions)


if __name__ == "__main__":
    main()
