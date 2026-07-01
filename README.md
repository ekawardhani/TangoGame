# Tango Card Game

Tango Card Game is a Japanese vocabulary game controlled by stretching poses. The game uses Cloudflare Workers AI to generate vocabulary questions and answer choices:
- Llama 3.3 70B Instruct for vocabulary questions and answer choices
- FLUX.1 Schnell for card image generation

The prompt uses GENKI I, Third Edition, Lessons 1–12 as the vocabulary reference.

## Files

```text
main.py              Starts the game
gameconfig.py        Game settings, ports, model names, and API settings
cardgenerator.py     Llama prompt, JSON parsing, and question validation
imagecache.py        FLUX image generation and card image cache
posedetector.py      Pose recognition rules
cameraloop.py        Webcam loop and gameplay input
gamelogic.py         Game rules, score, and round change
gamestate.py         Shared game state sent to HTML
server.py            HTTP server and WebSocket server
utils.py             Small helper functions
tangogame.html       Game display
card_assets/         Generated card images
requirements.txt     Required Python packages
```

## Important
The Python program reads Cloudflare credentials from environment variables. Please set your own Cloudflare credentials before running the game:

```bash
export cloudflare_ID="your_account_id"
export cloudflare_API="your_api_token"
```

## Setup
Install the required packages:

```bash
python3 -m pip install -r requirements.txt
```
Place `pose_landmarker.task` in the same folder as `main.py`.

## Run the Game

```bash
python3 main.py
```
Then open the browser link shown in the terminal.

## Pose Controls

```text
RELEASE  Arm rise pose             Start / next question
LEFT     Left side bending pose    Answer A
RIGHT    Right side bending pose   Answer B
UP       Forward arm pose          Answer C
DOWN     Back elbow pose           Answer D
```

## Notes for Testing

One game session contains 10 questions.
The player holds the selected pose for 15 seconds.
Correct answers give 10 points.
Wrong answers give 5 points.
