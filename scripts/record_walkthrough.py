"""Record the 5-minute CEO walkthrough as a screen recording that follows
08-executive-presentation/demo-script.md, for a voice-over by the presenter.

    python scripts/record_walkthrough.py OUT_DIR [--captions]

Writes OUT_DIR/walkthrough[-captioned].mp4 and OUT_DIR/walkthrough.srt.
--captions burns the script text into the picture (in the browser, so no
ffmpeg subtitle support is needed). Needs Playwright with local Chrome and
ffmpeg. The recording takes as long as the video: about 5 minutes.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_media import serve  # noqa: E402

# (start second, duration, screen, what to say) - same lines as demo-script.md
SCRIPT = [
    (0, 15, "deck:1", "Ilse, you asked three things: where to start, what it is worth, and how to do it without getting into trouble. Five minutes, three answers."),
    (15, 30, "deck:2", "Eleven people retype four thousand documents a month. We measured it: five and a half minutes each, and two in a hundred have an error that costs you later. That is the problem we solved first, because it ranked first whichever way your team weighted the criteria."),
    (45, 30, "deck:3", "Your company is ready to use AI, not yet to govern it. Documents are digital, the ISMS is certified, but there is no AI policy and a third of your people use public chatbots with customer data. That is the cheapest thing to fix, and it starts in week one."),
    (75, 45, "pilot:queue", "This is the pilot running on 220 test documents it never saw during tuning. Seven in ten go straight to the TMS. Here is one it stopped: the packing list says 6,943 kilos, the bill of lading 7,466. A clerk sees the reason in plain words and checks two fields, not the whole document."),
    (120, 45, "pilot:slider", "This slider is the trade-off your COO set in workshop three: at most one error in a hundred may slip through unseen. Today, by hand, it is two in a hundred. On the test set, nothing slipped through. On the tuning set, two did, both truck documents with a misread digit; the production build adds a check against the booking for exactly that."),
    (165, 30, "deck:5", "Why not just 'let AI read the documents'? Because that would have put 36 wrong documents into your TMS out of 220. The business rules your clerks apply in their heads are what makes it safe. We wrote them down and made them run."),
    (195, 35, "deck:7", "Your CFO's version: fifteen months to pay back, a hundred and ninety thousand euros over three years, on the cash view. The biggest lever is not the AI: it is whether you decide not to replace every second leaver. If you replace all of them, it still pays back, in about two years."),
    (230, 30, "deck:8", "Twelve months, five gates. You only decide on the first one today: eighty-five thousand euros. If shadow mode on real documents misses the bar in week thirteen, we stop."),
    (260, 25, "deck:9", "Your works council heard this plan before anyone else. No redundancies, no monitoring of individuals, and the one idea that would have been high-risk under the AI Act is parked, in writing."),
    (285, 15, "deck:10", "So: approve the first stage, endorse the people commitments, and let the steering group take the gates. I'm happy to take questions."),
]

CAPTION_JS = """(text) => {
  let el = document.getElementById('cap');
  if (!el) {
    el = document.createElement('div'); el.id = 'cap';
    el.style.cssText = 'position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1100px;width:calc(100% - 80px);'
      + 'background:rgba(11,11,11,.82);color:#fff;font:500 19px/1.4 Inter,system-ui,sans-serif;padding:10px 16px;border-radius:8px;z-index:9999;text-align:center';
    document.body.append(el);
  }
  el.textContent = text;
}"""

HIGHLIGHT_JS = """(sel) => {
  document.querySelectorAll('.tour-hl').forEach(e => e.classList.remove('tour-hl'));
  const el = document.querySelector(sel);
  if (el) { el.classList.add('tour-hl'); el.scrollIntoView({behavior: 'smooth', block: 'center'}); }
}"""


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path, starts, end):
    """Subtitles timed on the moments each segment really started in the recording."""
    lines = []
    for i, ((_, _, _, text), start) in enumerate(zip(SCRIPT, starts), 1):
        stop = starts[i] if i < len(starts) else end
        lines += [str(i), f"{srt_time(start)} --> {srt_time(stop)}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def record(out_dir, captions):
    httpd, base = serve()
    video_dir = Path(tempfile.mkdtemp())
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            ctx = browser.new_context(viewport={"width": 1280, "height": 720},
                                      record_video_dir=str(video_dir), record_video_size={"width": 1280, "height": 720})
            page = ctx.new_page()
            t0 = time.monotonic()
            starts = []
            current = None

            def open_page(path):
                nonlocal current
                if current != path:
                    page.goto(base + path)
                    page.evaluate("document.documentElement.dataset.theme = 'light'")
                    page.wait_for_timeout(700)
                    current = path

            def say(text):
                if captions:
                    page.evaluate(CAPTION_JS, text)

            for start, dur, screen, text in SCRIPT:
                kind, arg = screen.split(":")
                spent = 0
                if kind == "deck":
                    open_page("/deck/")
                else:
                    open_page("/pilot/")
                starts.append(time.monotonic() - t0)
                if kind == "deck":
                    open_page("/deck/")
                    page.evaluate(f"go({int(arg) - 1})")
                    say(text)
                    page.wait_for_timeout(dur * 1000)
                    continue
                open_page("/pilot/")
                say(text)
                if arg == "queue":
                    page.evaluate(HIGHLIGHT_JS, "#kpis")
                    page.wait_for_timeout(9000)
                    page.click('.tabs button[data-f="review"]')
                    page.evaluate("document.querySelector('.doc[data-id=\"DOC-0084\"]').scrollIntoView({block:'center'})")
                    page.click('.doc[data-id="DOC-0084"]')
                    page.evaluate(HIGHLIGHT_JS, "#why")
                    spent = 9000
                    page.wait_for_timeout(dur * 1000 - spent)
                else:  # slider: walk the threshold, then switch the layers off and on
                    page.evaluate(HIGHLIGHT_JS, "#ctl")
                    for value in ("0.5", "0.6", "0.75", "0.85", "0.95", "0.75"):
                        page.evaluate(f"(v) => {{ const s = document.getElementById('thr'); s.value = v; s.dispatchEvent(new Event('input')); }}", value)
                        page.wait_for_timeout(2500)
                        spent += 2500
                    page.evaluate(HIGHLIGHT_JS, "#kpis")
                    for box in ("#l-cross", "#l-single", "#l-thr"):
                        page.click(box)
                        page.wait_for_timeout(1500)
                        spent += 1500
                    page.wait_for_timeout(6000)
                    for box in ("#l-thr", "#l-single", "#l-cross"):
                        page.click(box)
                        page.wait_for_timeout(1500)
                        spent += 1500
                    page.wait_for_timeout(max(0, dur * 1000 - spent - 6000))
            page.wait_for_timeout(1000)
            end = time.monotonic() - t0
            video = page.video.path()
            ctx.close()
            browser.close()
        name = "walkthrough-captioned.mp4" if captions else "walkthrough.mp4"
        write_srt(out_dir / "walkthrough.srt", starts, end)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "23", "-movflags", "+faststart", str(out_dir / name)], check=True)
    finally:
        httpd.shutdown()
        shutil.rmtree(video_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir")
    parser.add_argument("--captions", action="store_true")
    args = parser.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    record(out, args.captions)
    print(json.dumps({"written": [p.name for p in sorted(out.iterdir())]}))


if __name__ == "__main__":
    main()
