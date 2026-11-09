"""Split a single-file slide export into a small, modular presentation folder.

The slide tool exports one self-contained HTML file (~1 MB, ~4,000 lines: a huge CSS
dump, base64 fonts and images, the player script and every slide on one line).
This script turns it into:

    presentation/
      index.html            short shell that loads the slides
      slides/NN-name.html   one file per slide, indented, with its speaker notes
      assets/deck.css       player styles + fonts (only what the slides use)
      assets/deck.js        slide player (navigation, builds, transitions)
      assets/loader.js      loads the slides into index.html, then starts the player
      assets/motion.json    builds and transitions of each slide
      assets/fonts/, assets/images/

Usage (from the repository root), after exporting the deck again:

    python presentation/split_deck.py path/to/TeachBack.html

The slides are loaded with fetch(), so open them through a web server:
`python -m server` (then /presentation/) or `python -m http.server -d presentation`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

# Minimal reset in place of the exported CSS dump: the slides use inline styles only.
RESET = """*, ::before, ::after { box-sizing: border-box; margin: 0; padding: 0; border: 0 solid; }
img, svg, video { display: block; max-width: 100%; }
img, video { height: auto; }
"""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "slide"


def ext_for(mime: str) -> str:
    return {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/svg+xml": "svg",
            "image/gif": "gif", "font/woff2": "woff2", "font/woff": "woff"}.get(mime, "bin")


class Assets:
    """Writes base64 data URIs to files, de-duplicated by content."""

    def __init__(self, root: Path):
        self.root = root
        self.seen: dict[str, str] = {}

    def save(self, mime: str, b64: str, folder: str, name: str) -> str:
        data = base64.b64decode(b64)
        digest = hashlib.sha1(data).hexdigest()[:8]
        if digest in self.seen:
            return self.seen[digest]
        rel = f"{folder}/{name}-{digest}.{ext_for(mime)}"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.seen[digest] = rel
        return rel


class Pretty(HTMLParser):
    """Puts each block element on its own line, but leaves text containers untouched.

    Whitespace inside text (white-space: pre-wrap) would change the rendering, so any
    element that holds text, and everything inside an <svg>, is copied verbatim.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.depth = 0
        self.verbatim = 0          # >0 while inside a text container or an svg

    def _raw(self) -> str:
        return self.get_starttag_text() or ""

    def _line(self, s: str) -> None:
        self.out.append("\n" + "  " * self.depth + s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        raw = self._raw()
        if self.verbatim:
            self.out.append(raw)
            if tag not in VOID:
                self.verbatim += 1
            return
        self._line(raw)
        if tag in VOID:
            return
        if tag == "svg" or "data-text-path" in a or re.search(r"white-space:\s*pre", a.get("style") or ""):
            self.verbatim = 1
        else:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        raw = self._raw()
        self.out.append(raw) if self.verbatim else self._line(raw)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.verbatim:
            self.out.append(f"</{tag}>")
            self.verbatim -= 1
            return
        self.depth -= 1
        self._line(f"</{tag}>")

    def handle_data(self, data):
        if self.verbatim or data.strip():
            self.out.append(data)

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_charref(self, name):
        self.out.append(f"&#{name};")

    @classmethod
    def format(cls, html: str) -> str:
        p = cls()
        p.feed(html)
        p.close()
        return "".join(p.out).strip() + "\n"


def main(src: Path) -> None:
    html = src.read_text(encoding="utf-8")
    head, body = html.split("<body", 1)
    styles = re.findall(r"<style[^>]*>(.*?)</style>", head, re.S)
    motion = re.search(r'<script type="application/json" id="deck-motion">(.*?)</script>', head, re.S).group(1)
    player = re.search(r"<script>(\(function.*?)</script>", head, re.S).group(1)
    title = re.search(r"<title>(.*?)</title>", head).group(1)
    links = re.findall(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', head)

    for sub in ("slides", "assets"):
        shutil.rmtree(OUT / sub, ignore_errors=True)
    assets = Assets(OUT / "assets")

    # --- CSS: the player styles + only the @font-face rules of the CSS dump --------------
    fonts = []
    for rule in re.findall(r"@font-face\s*\{[^}]*\}", styles[0]):
        family = slug(re.search(r"font-family:\s*['\"]?([^;'\"]+)", rule).group(1))
        weight = slug((re.search(r"font-weight:\s*([^;]+);", rule) or [None, "regular"])[1])

        def repl(m, family=family, weight=weight):
            rel = assets.save(m.group(1), m.group(2), "fonts", f"{family}-{weight}")
            return f'url("{rel}")'
        fonts.append(re.sub(r'url\("data:([^;]+);base64,([^"]+)"\)', repl, rule.strip()))
    player_css = styles[1].strip().replace("}", "}\n").replace("\n\n", "\n")
    (OUT / "assets" / "deck.css").write_text(
        "/* Generated by split_deck.py: fonts, reset and slide player styles. */\n\n"
        + "\n\n".join(fonts) + "\n\n" + RESET + "\n" + player_css, encoding="utf-8")

    # --- player, motion, loader --------------------------------------------------------------
    player = player.replace('JSON.parse(document.getElementById("deck-motion").textContent)', "window.DECK_MOTION")
    (OUT / "assets" / "deck.js").write_text("/* Slide player exported by the slide tool (unmodified apart from where it reads the motion data). */\n"
                                            + player + "\n", encoding="utf-8")
    m = json.loads(motion)
    slides_json = ",\n".join("  " + json.dumps(x, ensure_ascii=False) for x in m.pop("slides"))
    head_json = json.dumps(m, ensure_ascii=False)[:-1]
    (OUT / "assets" / "motion.json").write_text(f'{head_json}, "slides": [\n{slides_json}\n]}}\n', encoding="utf-8")
    shutil.copy(OUT / "loader.template.js", OUT / "assets" / "loader.js")

    # --- slides ---------------------------------------------------------------------------------
    main_open = re.search(r"<main[^>]*>", body).group(0)
    sections = re.findall(r'<section class="deck-slide".*?</section>', body, re.S)
    files = []
    for i, sec in enumerate(sections, 1):
        label = re.search(r'data-label="([^"]*)"', sec).group(1)

        def img(m, i=i):
            return "assets/" + assets.save(m.group(1), m.group(2), "images", f"slide-{i:02d}")
        sec = re.sub(r"data:(image/[a-z0-9+.-]+);base64,([A-Za-z0-9+/=]+)", img, sec)
        name = f"slides/{i:02d}-{slug(label)}.html"
        notes = re.search(r'data-speaker-notes="([^"]*)"', sec)
        header = f"<!-- Slide {i}: {label} -->\n"
        if notes:
            header += "<!-- Speaker notes: " + notes.group(1).replace("--", "—") + " -->\n"
        (OUT / name).parent.mkdir(exist_ok=True)
        (OUT / name).write_text(header + Pretty.format(sec), encoding="utf-8")
        files.append(name)

    main_tag = main_open.replace("<main", f'<main id="deck" data-slides="{" ".join(files)}"', 1)
    (OUT / "index.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{chr(10).join(links)}
<link rel="stylesheet" href="assets/deck.css">
</head>
<body>
<!-- Generated by split_deck.py. The slides are in slides/, loaded by assets/loader.js. -->
{main_tag}</main>
<div class="deck-pager" aria-hidden="true"></div>
<script src="assets/loader.js"></script>
</body>
</html>
""", encoding="utf-8")
    print(f"{len(files)} slides, {len(assets.seen)} assets written to {OUT.relative_to(Path.cwd()) if OUT.is_relative_to(Path.cwd()) else OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
