# Vimeo Screen Recorder — How It Works

This script automates recording Vimeo class videos on macOS using Chrome + AppleScript + the built-in Screenshot app.

## What the script does (per video)

1. **Opens the Vimeo URL** directly in a new Chrome tab, with `autoplay=1` appended so the video starts immediately
2. **Waits 8 seconds** for the page to fully load
3. **Toggles play/pause 3×** (odd number of presses guarantees the video is playing)
4. **Unmutes** the video using Vimeo's `M` keyboard shortcut
5. **Sets playback speed to 2×** via JavaScript: `document.querySelector("video").playbackRate = 2.0`
6. **Enables captions** with Vimeo's `C` keyboard shortcut
7. **Starts screen recording** using macOS's built-in Screenshot toolbar (`Cmd+Shift+5`), then presses Return to begin — macOS remembers the last mode (Record Entire Screen), so no menu navigation is needed
8. **Goes fullscreen** with Vimeo's `F` keyboard shortcut (Chrome re-activated first so focus is correct)
9. **Waits** for `RECORDING_DURATION` seconds (currently set to 10s for testing; change for real runs)
10. **Stops recording** with `Cmd+Ctrl+Esc` — macOS auto-saves the `.mov` to the Desktop
11. **Exits fullscreen** with Escape
12. **Closes the tab**

## Key configuration (top of `record_videos.py`)

| Variable | Default | Notes |
|---|---|---|
| `OUTPUT_DIR` | `~/Jingjing's docs/DI/class_recordings` | Where output files would go (naming only — macOS saves recordings to Desktop) |
| `LOG_FILE` | `~/Desktop/recording_log.txt` | Timestamped log of every action |
| `RECORDING_DURATION` | `10` | Seconds to record — set to full video length for real runs |
| `VIDEOS` | 2 entries | List of `{url, chapter, label}` dicts; add more as needed |

## Output filename format

`{chapter}_{label}.mov` — e.g., `3362_GENAI_AI_194_FT.mov`
(Note: macOS Screenshot app saves to Desktop with its own auto-name; rename manually after.)

## Requirements

- macOS with Screenshot app (built-in)
- Google Chrome
- Accessibility permissions granted to Terminal (System Settings → Privacy & Security → Accessibility)
- Screen Recording permission granted to Terminal

## Running

```bash
python3 record_videos.py
```

Do not touch the mouse or keyboard while the script runs — AppleScript controls the UI directly.

## Adding more videos

Add entries to the `VIDEOS` list in `record_videos.py`:

```python
{
    "url":     "https://vimeo.com/XXXXXXXXX/XXXXXXXXXX?fl=pl&fe=cm",
    "chapter": "CHAPTER_NUMBER",
    "label":   "GENAI_AI_194_FT",
},
```

Full list of urls for recording:
week5day2: https://vimeo.com/1183671754/f423ea0868?fl=pl&fe=cm
Week5day3: https://vimeo.com/1183673135/0784a66cf7?fl=pl&fe=cm
Week5day4: https://vimeo.com/1145864634/b5fd9ab988?fl=pl&fe=cm
Week5day42: https://vimeo.com/1145864406/893727518d?fl=pl&fe=cm
Week4day3: https://vimeo.com/1176901542/2bffc7da2d?fl=pl&fe=cm
Week4day2: https://vimeo.com/1176106685/7ce1852453?fl=pl&fe=cm
Week4day1: https://vimeo.com/1175410769/c9ca7799d7?fl=pl&fe=cm
Week3day5: https://vimeo.com/1141120784/b67c0bfeb7?fl=pl&fe=cm
Week3day4: https://vimeo.com/1173995212/a1ee01b480?fl=pl&fe=cm
Week3day3: https://vimeo.com/1167279681/2e44d46f23?fl=pl&fe=cm
Week3day2: https://vimeo.com/1173209663/914e5a42f8?fl=pl&fe=cm
Week3day21: https://vimeo.com/1172486435/032fc1409b?fl=pl&fe=cm
Week3day1: https://vimeo.com/1171706116/ebaadc947b?fl=pl&fe=cm






