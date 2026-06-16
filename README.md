# Class Recordings — Vimeo Auto-Recorder

Automates recording Vimeo class videos on macOS using Chrome, AppleScript, the built-in Screenshot app, and BlackHole for audio capture.

## How it works (per video)

1. Opens the Vimeo URL in a new Chrome tab with `autoplay=1`
2. Waits for the page to load, then clicks to focus the player
3. Plays, unmutes, and sets playback speed to 2×
4. Enables captions (`C` key)
5. Starts BlackHole audio capture (ffmpeg) and macOS screen recording simultaneously
6. Goes fullscreen and waits for the calculated recording duration
7. Stops both recordings, exits fullscreen, closes the tab
8. Merges the `.mov` screen capture + `.aac` audio into a final `.mp4` via ffmpeg
9. Cleans up the temp `.mov` and `.aac` files

## Requirements

- macOS with the built-in Screenshot app
- Google Chrome
- [ffmpeg](https://ffmpeg.org/) (`brew install ffmpeg`)
- [BlackHole 2ch](https://existential.audio/blackhole/) virtual audio driver
- Terminal granted **Accessibility** and **Screen Recording** permissions (System Settings → Privacy & Security)

## Configuration

Edit the top of `record_videos.py`:

| Variable | Default | Notes |
|---|---|---|
| `OUTPUT_DIR` | `~/Jingjing's docs/DI/class_recordings` | Where final `.mp4` files are saved |
| `LOG_FILE` | `~/Desktop/recording_log.txt` | Timestamped log of every action |
| `SPEED` | `2.0` | Playback speed (duration is auto-detected and adjusted) |
| `END_BUFFER` | `30` | Extra seconds added after the video ends |
| `SKIP_EXISTING` | `True` | Skips a video if its `.mp4` already exists |
| `BLACKHOLE_AUDIO_INDEX` | `"0"` | BlackHole device index from `ffmpeg -f avfoundation -list_devices true -i ""` |

## Running

```bash
python3 record_videos.py
```

Do not touch the mouse or keyboard while the script runs — AppleScript controls the UI directly.

## Output

Files are saved as `{chapter}_{label}.mp4`, e.g. `week5day2_GENAI_AI_194_FT.mp4`.

## Adding more videos

Add entries to the `VIDEOS` list in `record_videos.py`:

```python
{"url": "https://vimeo.com/XXXXXXXXX/XXXXXXXXXX?fl=pl&fe=cm", "chapter": "weekXdayY", "label": "GENAI_AI_194_FT"},
```

## Recorded videos

| Chapter | Label |
|---|---|
| week3day1 – week3day5 | GENAI_AI_194_FT |
| week4day1 – week4day3 | GENAI_AI_194_FT |
| week5day2 – week5day4 | GENAI_AI_194_FT |
