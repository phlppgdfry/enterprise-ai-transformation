"""Render the media files that cannot be built in CI without a browser.

    python scripts/render_media.py

Needs Playwright with a local Chrome (`pip install playwright`) and ffmpeg.
Writes:
  08-executive-presentation/board-presentation.pdf   the deck, one slide per page
  site/media/social-card.png                         1280x640 preview image
  site/media/pilot-tour.gif                          the pilot demo, for the README
Run it after the deck or the pilot results change; CI checks the files exist.
"""

import functools
import http.server
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(SITE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def social_card(page, base):
    page.set_viewport_size({"width": 1280, "height": 640})
    page.goto(base + "/")
    page.evaluate("""() => {
      document.documentElement.dataset.theme = 'light';
      document.querySelector('header.top').remove();
      document.querySelectorAll('section:not(:first-of-type), .btns, .disclaimer, footer').forEach(e => e.remove());
      document.querySelector('main').style.paddingTop = '56px';
    }""")
    page.wait_for_timeout(600)
    page.screenshot(path=str(SITE / "media" / "social-card.png"))


def deck_pdf(page, base):
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto(base + "/deck/")
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    page.wait_for_timeout(800)
    page.pdf(path=str(ROOT / "08-executive-presentation" / "board-presentation.pdf"),
             width="1280px", height="720px", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})


def pilot_gif(page, base):
    frames = Path(tempfile.mkdtemp())
    page.set_viewport_size({"width": 1200, "height": 760})
    page.goto(base + "/pilot/")
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    page.wait_for_timeout(900)
    n = 0

    def snap(times=1):
        nonlocal n
        for _ in range(times):
            page.screenshot(path=str(frames / f"f{n:03d}.png"))
            n += 1

    page.evaluate("window.scrollTo(0, 250)")
    snap(6)
    for box in ("#l-cross", "#l-single", "#l-thr"):        # switch the safety layers off
        page.click(box)
        page.wait_for_timeout(200)
        snap(4)
    snap(6)
    for box in ("#l-thr", "#l-single", "#l-cross"):        # and back on
        page.click(box)
        page.wait_for_timeout(200)
        snap(4)
    page.evaluate("window.scrollTo(0, 560)")
    page.click('.doc[data-id="DOC-0084"]') if page.query_selector('.doc[data-id="DOC-0084"]') else None
    page.wait_for_timeout(300)
    snap(10)
    out = SITE / "media" / "pilot-tour.gif"
    palette = frames / "palette.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "4", "-i", str(frames / "f%03d.png"),
                    "-vf", "scale=900:-1:flags=lanczos,palettegen", str(palette)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "4", "-i", str(frames / "f%03d.png"),
                    "-i", str(palette), "-lavfi", "scale=900:-1:flags=lanczos[x];[x][1:v]paletteuse", str(out)], check=True)
    shutil.rmtree(frames)


def main():
    httpd, base = serve()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page()
            deck_pdf(page, base)
            social_card(page, base)
            pilot_gif(page, base)
            browser.close()
    finally:
        httpd.shutdown()
    print("wrote board-presentation.pdf, social-card.png, pilot-tour.gif")


if __name__ == "__main__":
    main()
