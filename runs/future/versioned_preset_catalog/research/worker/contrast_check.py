#!/usr/bin/env python3
"""Compute WCAG relative-luminance contrast ratios for candidate text pairs."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
PAIRS = {
    "review_body": ["#17212B", "#F3F6FA"],
    "review_surface_text": ["#1F2937", "#FFFFFF"],
    "review_muted": ["#475569", "#F3F6FA"],
    "action_on_white": ["#1D4ED8", "#FFFFFF"],
    "action_button_text": ["#FFFFFF", "#1D4ED8"],
    "selected_text": ["#1E3A8A", "#DBEAFE"],
    "error_text": ["#991B1B", "#FEF2F2"],
    "success_text": ["#065F46", "#ECFDF5"],
    "warning_text": ["#854D0E", "#FFFBEB"],
    "focus_on_surface": ["#005FCC", "#FFFFFF"],
    "focus_on_canvas": ["#005FCC", "#F3F6FA"],
    "focus_on_stock_canvas": ["#005FCC", "#F8FAFC"],
    "focus_on_reader_canvas": ["#005FCC", "#FBFAF7"],
    "muted_on_stock_canvas": ["#475569", "#F8FAFC"],
    "muted_on_reader_canvas": ["#475569", "#FBFAF7"],
    "stock_canvas": ["#1F2937", "#F8FAFC"],
    "reader_body": ["#2F2D2A", "#FBFAF7"],
    "reader_annotation": ["#3A311E", "#FFF1C2"],
}

def channel(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(hex_color):
    rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    r, g, b = [channel(c) for c in rgb]
    return 0.2126*r + 0.7152*g + 0.0722*b

def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)

results = []
for name, (fg, bg) in PAIRS.items():
    results.append({"name": name, "foreground": fg, "background": bg, "ratio": round(contrast(fg, bg), 2)})
(ROOT / "contrast_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
for row in results:
    print(f"{row['name']}: {row['foreground']} on {row['background']} = {row['ratio']}:1")
