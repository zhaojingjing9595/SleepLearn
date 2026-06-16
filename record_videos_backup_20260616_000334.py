#!/usr/bin/env python3
"""
Automated screen recording of Vimeo videos.
Opens direct Vimeo URLs in Chrome, sets 2x speed, goes fullscreen,
then records using the macOS built-in Screenshot app.
"""

import subprocess
import time
import os
import datetime
import sys

# ── Configuration ────────────────────────────────────────────────
OUTPUT_DIR  = "/Users/jingjingzhao/Jingjing's docs/DI/class_recordings"
LOG_FILE    = os.path.expanduser("~/Desktop/recording_log.txt")
RECORDING_DURATION = 10   # seconds — change to full video length for real runs

VIDEOS = [
    {
        "url":     "https://vimeo.com/1172486435/032fc1409b?fl=pl&fe=cm",
        "chapter": "3362",
        "label":   "GENAI_AI_194_FT",
    },
    {
        "url":     "https://vimeo.com/1173209663/914e5a42f8?fl=pl&fe=cm",
        "chapter": "4442",
        "label":   "GENAI_AI_194_FT",
    },
]

# ── Helpers ──────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def osa(script: str, desc: str = "") -> tuple:
    """Run AppleScript. Returns (success, stdout)."""
    if desc:
        log(f"  > {desc}")
    r = subprocess.run(["osascript", "-e", script],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        log(f"    WARNING: {r.stderr.strip()}")
        return False, r.stderr.strip()
    out = r.stdout.strip()
    if out and out != "missing value":
        log(f"    {out}")
    return True, out


def run_js(js: str, desc: str = "") -> tuple:
    """Execute JavaScript in Chrome's active tab."""
    js_escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Google Chrome"
    set result to execute active tab of front window javascript "{js_escaped}"
    return result
end tell
'''
    return osa(script, desc)


def click(x: int, y: int, desc: str = ""):
    """Click at screen coordinates via System Events."""
    log(f"  click ({x}, {y}) {desc}")
    osa(f'''
tell application "System Events"
    click at {{{x}, {y}}}
end tell
''')
    time.sleep(0.3)


def key(keystroke: str, modifiers: list = None, desc: str = ""):
    """Send a keystroke, optionally with modifier keys."""
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(modifiers) + "}"
    script = f'tell application "System Events" to keystroke "{keystroke}"{mod_str}'
    osa(script, desc)


def keycode(code: int, modifiers: list = None, desc: str = ""):
    """Send a key by key code."""
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(modifiers) + "}"
    script = f'tell application "System Events" to key code {code}{mod_str}'
    osa(script, desc)


def get_screen_size() -> tuple:
    """Return (width, height) of main display."""
    success, out = osa('''
tell application "Finder"
    set b to bounds of window of desktop
    return (item 3 of b as string) & "x" & (item 4 of b as string)
end tell
''', "Getting screen size")
    if success and "x" in out:
        w, h = out.split("x")
        return int(w), int(h)
    return 1920, 1080   # safe fallback


def chrome_window_bounds() -> tuple:
    """Return (x1, y1, x2, y2) of Chrome's front window."""
    _, out = osa('''
tell application "Google Chrome"
    set b to bounds of front window
    return (item 1 of b as string) & "," & (item 2 of b as string) & "," & (item 3 of b as string) & "," & (item 4 of b as string)
end tell
''', "Getting Chrome window bounds")
    if out.count(",") == 3:
        x1, y1, x2, y2 = [int(v) for v in out.split(",")]
        return x1, y1, x2, y2
    return 0, 25, 1680, 1080   # fallback: assume left monitor


def chrome_content_origin() -> tuple:
    """Return (x, y) of Chrome's content area top-left (window pos + toolbar)."""
    x1, y1, x2, y2 = chrome_window_bounds()
    toolbar = 70   # tab bar + address bar
    return x1, y1 + toolbar


# ── Screen recording via macOS Screenshot app (Cmd+Shift+5) ──────

def start_screenshot_recording():
    """Open Screenshot toolbar with Cmd+Shift+5, then press Return to start recording.
    macOS remembers the last mode (Record Entire Screen), so Return starts it immediately."""
    log("  Opening Screenshot toolbar (Cmd+Shift+5)")
    osa('tell application "System Events" to key code 23 using {command down, shift down}')
    time.sleep(2)
    log("  Pressing Return to start recording")
    osa('tell application "System Events" to key code 36')   # Return key
    time.sleep(3)   # 3-second countdown
    log("  Recording started.")


def stop_screenshot_recording():
    """Stop recording with Cmd+Ctrl+Esc — macOS auto-saves to Desktop."""
    log("  Stopping recording (Cmd+Ctrl+Esc)")
    osa('tell application "System Events" to key code 53 using {command down, control down}')
    time.sleep(2)
    log("  Recording stopped and saved to Desktop.")


# ── Main video workflow ──────────────────────────────────────────

def record_video(entry: dict):
    url     = entry["url"]
    chapter = entry["chapter"]
    label   = entry["label"]
    out     = os.path.join(OUTPUT_DIR, f"{chapter}_{label}.mov")

    log("=" * 60)
    log(f"START  chapter={chapter}  label={label}")
    log(f"URL:   {url}")
    log(f"OUT:   {out}")
    log("=" * 60)

    # 1. Open URL in Chrome
    # Append autoplay=1 so video starts without needing a click
    autoplay_url = url + ("&" if "?" in url else "?") + "autoplay=1"
    osa(f'''
tell application "Google Chrome"
    activate
    if (count of windows) = 0 then
        make new window
        set URL of active tab of front window to "{autoplay_url}"
    else
        tell front window to make new tab with properties {{URL:"{autoplay_url}"}}
    end if
end tell
''', f"Opening URL in new Chrome tab (autoplay)")
    log("Waiting 8s for page to load…")
    time.sleep(8)

    # 2. Activate Chrome and press Space 3 times to ensure video is playing
    #    (first press plays, second pauses if already playing, third plays again —
    #     doing odd number ensures we end up playing)
    log("Toggling play/pause 3× to confirm video is playing…")
    for i in range(3):
        osa('tell application "Google Chrome" to activate\ndelay 0.2\ntell application "System Events" to keystroke " "',
            f"Space #{i+1}")
        time.sleep(1.5)

    # Unmute (Vimeo shortcut: M toggles mute)
    log("Unmuting video (M key)")
    osa('tell application "Google Chrome" to activate\ndelay 0.2\ntell application "System Events" to keystroke "m"',
        "Unmute")
    time.sleep(0.5)

    # 4. Set speed to 2x via JavaScript (works directly on vimeo.com — no iframe blocking)
    log("Setting playback speed to 2x via JavaScript…")
    run_js('document.querySelector("video").playbackRate = 2.0', "Set playbackRate=2.0")
    time.sleep(0.5)

    # 5. Press C for captions
    log("Pressing C for captions")
    osa('tell application "Google Chrome" to activate\ndelay 0.2\ntell application "System Events" to keystroke "c"',
        "Captions shortcut")
    time.sleep(0.5)

    # 6. Start Screenshot recording BEFORE fullscreen (click works outside fullscreen)
    start_screenshot_recording()

    # 7. Press F for fullscreen — give Chrome time to regain focus after Screenshot toolbar
    log("Pressing F for fullscreen")
    osa('tell application "Google Chrome" to activate')
    time.sleep(1.5)   # wait for Chrome to fully regain focus after Screenshot toolbar
    osa('tell application "System Events" to keystroke "f"', "Fullscreen shortcut")
    log("Waiting 3s for fullscreen…")
    time.sleep(3)

    # 8. Record
    log(f"Recording for {RECORDING_DURATION}s…")
    time.sleep(RECORDING_DURATION)

    # 9. Stop recording (macOS saves the file automatically)
    stop_screenshot_recording()

    # 10. Exit fullscreen
    keycode(53, desc="Escape – exit fullscreen")
    time.sleep(1)

    # 11. Close this tab
    log("Closing tab")
    osa('tell application "Google Chrome" to tell front window to close active tab')

    log(f"DONE chapter {chapter}")


def main():
    log("=" * 60)
    log("Vimeo Screen Recorder")
    log(f"Output dir : {OUTPUT_DIR}")
    log(f"Duration   : {RECORDING_DURATION}s per video")
    log("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i, entry in enumerate(VIDEOS):
        log(f"\n── Video {i+1}/{len(VIDEOS)} ──")
        try:
            record_video(entry)
        except KeyboardInterrupt:
            log("Interrupted.")
            sys.exit(0)
        except Exception as e:
            import traceback
            log(f"ERROR: {e}\n{traceback.format_exc()}")
        if i < len(VIDEOS) - 1:
            log("Waiting 3s before next video…")
            time.sleep(3)

    log("\n" + "=" * 60)
    log("All done.")
    log("=" * 60)


if __name__ == "__main__":
    main()
