#!/usr/bin/env python3
"""
Automated screen recording of Vimeo videos.
- Screen: macOS built-in Screenshot app (Cmd+Shift+5) → saves .mov to Desktop
- Audio:  ffmpeg capturing BlackHole 2ch in parallel → saves .aac
- Merge:  ffmpeg combines video + audio into final .mp4 in OUTPUT_DIR
"""

import subprocess
import time
import os
import glob
import datetime
import sys
import signal

# ── Configuration ────────────────────────────────────────────────
OUTPUT_DIR  = "/Users/jingjingzhao/Jingjing's docs/DI/class_recordings"
LOG_FILE    = os.path.expanduser("~/Desktop/recording_log.txt")
BLACKHOLE_AUDIO_INDEX = "0"   # "BlackHole 2ch" — from: ffmpeg -f avfoundation -list_devices true -i ""
SPEED = 2.0          # playback speed
END_BUFFER = 30      # extra seconds after video ends before stopping recording
SKIP_EXISTING = True # skip video if .mp4 already exists in OUTPUT_DIR

VIDEOS = [
    {"url": "https://vimeo.com/1183671754/f423ea0868?fl=pl&fe=cm",  "chapter": "week5day2",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1183673135/0784a66cf7?fl=pl&fe=cm",  "chapter": "week5day3",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1145864634/b5fd9ab988?fl=pl&fe=cm",  "chapter": "week5day4",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1145864406/893727518d?fl=pl&fe=cm",  "chapter": "week5day42", "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1176901542/2bffc7da2d?fl=pl&fe=cm",  "chapter": "week4day3",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1176106685/7ce1852453?fl=pl&fe=cm",  "chapter": "week4day2",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1175410769/c9ca7799d7?fl=pl&fe=cm",  "chapter": "week4day1",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1141120784/b67c0bfeb7?fl=pl&fe=cm",  "chapter": "week3day5",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1173995212/a1ee01b480?fl=pl&fe=cm",  "chapter": "week3day4",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1167279681/2e44d46f23?fl=pl&fe=cm",  "chapter": "week3day3",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1173209663/914e5a42f8?fl=pl&fe=cm",  "chapter": "week3day2",  "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1172486435/032fc1409b?fl=pl&fe=cm",  "chapter": "week3day21", "label": "GENAI_AI_194_FT"},
    {"url": "https://vimeo.com/1171706116/ebaadc947b?fl=pl&fe=cm",  "chapter": "week3day1",  "label": "GENAI_AI_194_FT"},
]

# ── Helpers ──────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def osa(script: str, desc: str = "") -> tuple:
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
    js_escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Google Chrome"
    set result to execute active tab of front window javascript "{js_escaped}"
    return result
end tell
'''
    return osa(script, desc)


def keypress(key_char: str, desc: str = ""):
    script = f'tell application "Google Chrome" to activate\ndelay 0.3\ntell application "System Events" to keystroke "{key_char}"'
    osa(script, desc)
    time.sleep(0.5)


def chrome_window_bounds() -> tuple:
    _, out = osa('''
tell application "Google Chrome"
    set b to bounds of front window
    return (item 1 of b as string) & "," & (item 2 of b as string) & "," & (item 3 of b as string) & "," & (item 4 of b as string)
end tell
''', "Getting Chrome window bounds")
    if out.count(",") == 3:
        x1, y1, x2, y2 = [int(v) for v in out.split(",")]
        return x1, y1, x2, y2
    return 0, 25, 1680, 1080


def click_at(x: int, y: int, desc: str = ""):
    log(f"  click ({x}, {y}) {desc}")
    osa(f'tell application "System Events" to click at {{{x}, {y}}}')
    time.sleep(0.4)


def get_video_duration() -> float:
    """Return video duration in seconds via JS. Returns 0 if not found."""
    success, out = run_js('var v=document.querySelector("video"); v ? v.duration : 0', "Getting video duration")
    try:
        val = float(out)
        if val > 0 and not __import__('math').isnan(val) and not __import__('math').isinf(val):
            return val
    except Exception:
        pass
    return 0


def click_video_center():
    """Click the video element center to focus the Vimeo player."""
    success, out = run_js(
        'var v=document.querySelector("video"); if(v){var r=v.getBoundingClientRect(); Math.round(r.left)+","+Math.round(r.top)+","+Math.round(r.width)+","+Math.round(r.height)}else{"none"}',
        "Getting video element bounding rect"
    )
    if not success or out == "none" or "," not in out:
        log("  WARNING: could not find video element, clicking screen center as fallback")
        x1, y1, x2, y2 = chrome_window_bounds()
        click_at((x1 + x2) // 2, (y1 + y2) // 2, "screen center fallback")
        return

    left, top, width, height = [int(v) for v in out.split(",")]
    x1, y1, _, _ = chrome_window_bounds()
    toolbar = 70

    _, scroll = run_js('window.scrollX+","+window.scrollY', "Getting scroll position")
    scroll_x, scroll_y = (0, 0)
    if scroll and "," in scroll:
        scroll_x, scroll_y = [int(v) for v in scroll.split(",")]

    screen_x = x1 + left + width // 2 - scroll_x
    screen_y = y1 + toolbar + top + height // 2 - scroll_y
    click_at(screen_x, screen_y, "video center (to focus player)")


# ── macOS Screenshot app (screen video) ─────────────────────────

def start_screenshot_recording():
    log("  Opening Screenshot toolbar (Cmd+Shift+5)")
    osa('tell application "System Events" to key code 23 using {command down, shift down}')
    time.sleep(2)
    log("  Pressing Return to start recording")
    osa('tell application "System Events" to key code 36')
    time.sleep(3)   # 3-second countdown
    log("  Screenshot recording started.")


def stop_screenshot_recording():
    log("  Stopping Screenshot recording (Cmd+Ctrl+Esc)")
    osa('tell application "System Events" to key code 53 using {command down, control down}')
    time.sleep(3)   # give macOS time to finish writing the file
    log("  Screenshot recording stopped — file saved to Desktop.")


def find_latest_desktop_mov(before_ts: float) -> str:
    """Return the newest .mov on Desktop created after before_ts."""
    desktop = os.path.expanduser("~/Desktop")
    movs = glob.glob(os.path.join(desktop, "*.mov"))
    new_movs = [f for f in movs if os.path.getmtime(f) >= before_ts]
    if not new_movs:
        return None
    return max(new_movs, key=os.path.getmtime)


# ── ffmpeg audio-only capture (BlackHole) ───────────────────────

_ffmpeg_proc = None

def start_audio_recording(audio_path: str):
    global _ffmpeg_proc
    log(f"  Starting BlackHole audio capture → {audio_path}")
    cmd = [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-i", f":{BLACKHOLE_AUDIO_INDEX}",   # audio only, no video
        "-acodec", "aac",
        "-b:a", "192k",
        audio_path,
    ]
    _ffmpeg_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    log("  Audio capture started.")


def stop_audio_recording():
    global _ffmpeg_proc
    if _ffmpeg_proc is None:
        return
    log("  Stopping audio capture…")
    try:
        _ffmpeg_proc.stdin.write(b"q")
        _ffmpeg_proc.stdin.flush()
    except Exception:
        _ffmpeg_proc.send_signal(signal.SIGINT)
    try:
        _ffmpeg_proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        _ffmpeg_proc.kill()
    _ffmpeg_proc = None
    log("  Audio capture stopped.")


# ── Merge video + audio ──────────────────────────────────────────

def merge_video_audio(video_path: str, audio_path: str, output_path: str):
    log(f"  Merging video + audio → {output_path}")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  ERROR merging: {r.stderr[-500:]}")
    else:
        log(f"  Merge done → {output_path}")


# ── Main video workflow ──────────────────────────────────────────

def record_video(entry: dict):
    url     = entry["url"]
    chapter = entry["chapter"]
    label   = entry["label"]
    final   = os.path.join(OUTPUT_DIR, f"{chapter}_{label}.mp4")
    audio   = os.path.join(OUTPUT_DIR, f"{chapter}_{label}_audio.aac")

    log("=" * 60)
    log(f"START  chapter={chapter}  label={label}")
    log(f"URL:   {url}")
    log(f"OUT:   {final}")
    log("=" * 60)

    if SKIP_EXISTING and os.path.exists(final):
        log(f"SKIP — file already exists: {final}")
        return

    # 1. Open URL in Chrome (autoplay)
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
''', "Opening URL in new Chrome tab")
    log("Waiting 8s for page to load…")
    time.sleep(8)

    # 2. Click video to focus player
    log("Clicking video center to focus player…")
    click_video_center()
    time.sleep(1)

    # 3. Play (Space)
    keypress(" ", "Play (Space)")
    time.sleep(1)

    # 4. Unmute (M)
    keypress("m", "Unmute")

    # 5. Speed 2x via JS + detect duration
    run_js(f'document.querySelector("video").playbackRate = {SPEED}', "Set playbackRate")
    time.sleep(0.5)

    duration = get_video_duration()
    if duration > 0:
        recording_duration = int(duration / SPEED) + END_BUFFER
        log(f"Video duration: {int(duration)}s → recording for {recording_duration}s at {SPEED}x")
    else:
        recording_duration = 7200  # 2h fallback if duration unknown
        log(f"WARNING: could not detect duration, using 2h fallback")

    # 6. Captions (C)
    keypress("c", "Captions")

    # 7. Start audio capture (BlackHole) + Screenshot screen recording simultaneously
    start_audio_recording(audio)
    snap_before = time.time()
    start_screenshot_recording()

    # 8. Re-focus Chrome and go fullscreen (F)
    log("Clicking video to re-focus before fullscreen…")
    click_video_center()
    time.sleep(0.5)
    keypress("f", "Fullscreen")
    log("Waiting 3s for fullscreen…")
    time.sleep(3)

    # 9. Record
    log(f"Recording for {recording_duration}s…")
    time.sleep(recording_duration)

    # 10. Stop both recordings
    stop_screenshot_recording()
    stop_audio_recording()

    # 11. Exit fullscreen
    osa('tell application "System Events" to key code 53', "Escape – exit fullscreen")
    time.sleep(1)

    # 12. Close tab
    log("Closing tab…")
    osa('tell application "Google Chrome" to tell front window to close active tab')

    # 13. Find the .mov Screenshot app saved to Desktop and merge with audio
    log("Looking for Screenshot .mov on Desktop…")
    time.sleep(2)
    video_mov = find_latest_desktop_mov(snap_before)
    if video_mov:
        log(f"  Found: {video_mov}")
        merge_video_audio(video_mov, audio, final)
        # clean up temp audio file and original .mov
        os.remove(audio)
        os.remove(video_mov)
        log(f"  Cleaned up temp files.")
    else:
        log("  WARNING: could not find Screenshot .mov on Desktop — skipping merge.")
        log(f"  Audio saved at: {audio}")

    log(f"DONE chapter {chapter} → {final}")


def main():
    log("=" * 60)
    log("Vimeo Screen Recorder (Screenshot app + BlackHole audio)")
    log(f"Output dir : {OUTPUT_DIR}")
    log(f"Speed      : {SPEED}x  (duration auto-detected per video)")
    log("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i, entry in enumerate(VIDEOS):
        log(f"\n── Video {i+1}/{len(VIDEOS)} ──")
        try:
            record_video(entry)
        except KeyboardInterrupt:
            log("Interrupted.")
            stop_audio_recording()
            sys.exit(0)
        except Exception as e:
            import traceback
            log(f"ERROR: {e}\n{traceback.format_exc()}")
            stop_audio_recording()
        if i < len(VIDEOS) - 1:
            log("Waiting 3s before next video…")
            time.sleep(3)

    log("\n" + "=" * 60)
    log("All done.")
    log("=" * 60)


if __name__ == "__main__":
    main()
