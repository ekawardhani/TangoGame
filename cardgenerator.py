import json
import random
import re
import requests

from gameconfig import (
    cloudflare_ID,
    cloudflare_API,
    CF_TEXT_MODEL,
    round_session,
    cloudflare,
)


def cloudflare_run(model: str, payload: dict, timeout: int = 90):
    """Send one request to a Cloudflare Workers AI model."""
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{cloudflare_ID}/ai/run/{model}"
    )
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {cloudflare_API}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    body = response.json()
    if not body.get("success", False):
        raise RuntimeError(body.get("errors") or "Cloudflare AI request failed")
    return body.get("result", {})


def repair_mojibake(value: str) -> str:
    """Try to repair broken Japanese text such as 'ã'."""
    if "ã" in value or "Â" in value:
        try:
            return value.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return value


def normalize_hiragana(raw) -> str:
    """Read a value and check that it is hiragana only."""
    if isinstance(raw, dict):
        raw = raw.get("jp", "")
    value = repair_mojibake(str(raw).strip())
    if not re.fullmatch(r"[ぁ-ゖー]+", value):
        raise ValueError("Answer must use hiragana only")
    return value


def balance_answer_positions(questions: list) -> None:
    """Shuffle correct answers so they are balanced across A, B, C, and D."""
    full_sets, remainder = divmod(len(questions), 4)
    positions = list(range(4)) * full_sets
    positions.extend(random.sample(range(4), remainder))
    random.shuffle(positions)

    for question, correct_position in zip(questions, positions):
        target_jp = question["target"]["jp"]
        correct = next(item for item in question["choices"] if item["jp"] == target_jp)
        wrong = [item for item in question["choices"] if item["jp"] != target_jp]
        random.shuffle(wrong)
        wrong.insert(correct_position, correct)
        question["choices"] = wrong

    labels = ["ABCD"[position] for position in positions]
    print("[AI] Correct answer positions:", " ".join(labels))


def parse_ai_question(generated: dict) -> dict:
    """Convert Llama JSON into the question format used by the game."""
    if not isinstance(generated, dict):
        raise ValueError("AI response must be a JSON object")

    target_jp = normalize_hiragana(generated.get("target_jp", ""))
    target_romaji = repair_mojibake(str(generated.get("target_romaji", "")).strip().lower())
    target_meaning = repair_mojibake(str(generated.get("target_meaning", "")).strip().lower())
    choice_jp = [normalize_hiragana(item) for item in generated.get("choices", [])]
    image_prompt = str(generated.get("image_prompt", "")).strip()

    if not target_romaji or not target_meaning or not image_prompt:
        raise ValueError("Target fields cannot be empty")
    if not re.fullmatch(r"[a-z][a-z '-]*", target_romaji):
        raise ValueError("Romaji must use Latin letters")
    if not re.fullmatch(r"[a-z][a-z '-]*", target_meaning):
        raise ValueError("Meaning must use simple English text")
    if len(choice_jp) != 4 or len(set(choice_jp)) != 4:
        raise ValueError("There must be four different choices")
    if choice_jp.count(target_jp) != 1:
        raise ValueError("The correct target must appear exactly once")

    target = {
        "jp": target_jp,
        "romaji": target_romaji,
        "meaning": target_meaning,
        "image_prompt": image_prompt,
    }
    choices = [
        {
            "jp": jp,
            "romaji": target_romaji if jp == target_jp else "",
            "meaning": target_meaning if jp == target_jp else "",
        }
        for jp in choice_jp
    ]
    return {"target": target, "choices": choices}


def generate_ai_session() -> list:
    """Generate ten valid GENKI I-based vocabulary questions."""
    if not cloudflare:
        raise RuntimeError(
            "AI mode requires cloudflare_ID and cloudflare_API. Please set them in Terminal."
        )

    schema = {
        "type": "object",
        "properties": {
            "target_jp": {"type": "string"},
            "target_romaji": {"type": "string"},
            "target_meaning": {"type": "string"},
            "choices": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {"type": "string"},
            },
            "image_prompt": {"type": "string"},
        },
        "required": [
            "target_jp",
            "target_romaji",
            "target_meaning",
            "choices",
            "image_prompt",
        ],
    }

    questions = []
    used_targets = set()

    for question_number in range(1, round_session + 1):
        excluded = ", ".join(sorted(used_targets)) or "none"
        prompt = (
            "Create ONE Japanese vocabulary multiple-choice question using GENKI I, "
            "Third Edition, Lessons 1-12 as the vocabulary reference. "
            "Use a real, common, concrete noun taught in GENKI I that can be clearly shown "
            "in one picture. Do not use vocabulary outside GENKI I. "
            "Check the Japanese spelling, romaji, and English meaning before answering. "
            "Never invent a Japanese word. Write all Japanese words in hiragana only. "
            "Examples of suitable GENKI I vocabulary pairs are ほん / hon / book, "
            "かさ / kasa / umbrella, and とけい / tokei / watch. "
            "The target must not be one of these previous targets: "
            f"{excluded}. Provide target_jp, target_romaji, and target_meaning. "
            "choices must contain target_jp exactly once plus three different real nouns "
            "from GENKI I written in hiragana. Avoid near-synonyms, ambiguous meanings, "
            "and words with the same pronunciation. image_prompt must clearly show the "
            "target as a bright educational cartoon with no text, letters, or words."
        )
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful Japanese language teacher familiar with GENKI I, "
                        "Third Edition, Lessons 1-12. Use GENKI I as the vocabulary reference "
                        "and return only accurate vocabulary in the requested JSON schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_schema", "json_schema": schema},
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 700,
        }

        last_error = None
        for attempt in range(1, 5):
            data = {}
            try:
                result = cloudflare_run(CF_TEXT_MODEL, payload, timeout=90)
                raw = result.get("response", result)
                data = json.loads(raw) if isinstance(raw, str) else raw
                question = parse_ai_question(data.get("question", data))
                target_jp = question["target"]["jp"]
                if target_jp in used_targets:
                    raise ValueError("AI repeated a target word")
                questions.append(question)
                used_targets.add(target_jp)
                print(
                    f"[AI] Question {question_number}/{round_session}: "
                    f"{target_jp} = {question['target']['meaning']}"
                )
                break
            except Exception as exc:
                last_error = exc
                print(f"[AI] Question {question_number}, attempt {attempt} failed:", exc)
                if data:
                    print("[AI DEBUG] Response preview:", json.dumps(data, ensure_ascii=False)[:700])
        else:
            raise RuntimeError(f"AI could not create question {question_number}: {last_error}")

    random.shuffle(questions)
    balance_answer_positions(questions)
    return questions
