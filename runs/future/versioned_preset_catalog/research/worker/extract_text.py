#!/usr/bin/env python3
"""Extract human-readable text from the already-fetched HTML snapshots."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "blockquote", "dt", "dd", "pre"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip:
            self.skip -= 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "blockquote", "dt", "dd", "pre"):
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

for path in sorted((ROOT / "source_snapshots").glob("*.html")):
    parser = TextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    text = re.sub(r"[\t\r ]+", " ", "".join(parser.parts))
    text = re.sub(r" *\n+ *", "\n", text).strip()
    out = path.with_suffix(".txt")
    out.write_text(text + "\n", encoding="utf-8")
    print(f"=== {path.stem}: {out.stat().st_size} chars ===")
    patterns = {
        "wcag_use_of_color": ("color is not used as the only visual means", "additional visual cue", "form fields", "link", "status"),
        "wcag_contrast_minimum": ("4.5:1", "3:1", "large-scale", "inactive user interface"),
        "wcag_focus_visible": ("keyboard focus", "visible focus", "not obscure", "focus indicator"),
        "mdn_reduced_motion": ("prefers-reduced-motion", "reduce motion", "non-essential motion", "reduce"),
        "mdn_dialog": ("modal dialog", "showModal()", "Escape", "focus", "close"),
        "android_system_bars": ("status bar", "navigation bar", "system bars", "edge-to-edge", "insets"),
        "refero_styles_lead": ("DESIGN.md", "colors", "spacing", "components"),
    }.get(path.stem, ())
    lines = text.splitlines()
    seen = set()
    for phrase in patterns:
        matches = [i for i, line in enumerate(lines) if phrase.lower() in line.lower()]
        for i in matches[:2]:
            start, end = max(0, i-1), min(len(lines), i+2)
            excerpt = " ".join(lines[start:end])
            if excerpt not in seen:
                print(f"[{phrase}] {excerpt[:1000]}")
                seen.add(excerpt)
