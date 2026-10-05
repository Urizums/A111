#!/usr/bin/env python3
"""Fetch the bounded source set and preserve each exact response body."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "source_snapshots"
URLS = {
    "refero_styles_lead": "https://styles.refero.design/",
    "wcag_use_of_color": "https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html",
    "wcag_contrast_minimum": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
    "wcag_focus_visible": "https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html",
    "mdn_reduced_motion": "https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion",
    "mdn_dialog": "https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog",
    "android_system_bars": "https://developer.android.com/design/ui/mobile/guides/foundations/system-bars",
}

results = []
for key, url in URLS.items():
    result = {"key": key, "url": url, "accessed_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; bounded-design-research/1.0)"})
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read()
                result["status"] = response.status
                result["final_url"] = response.geturl()
                result["headers"] = dict(response.headers.items())
        except HTTPError as error:
            body = error.read()
            result["status"] = error.code
            result["final_url"] = error.geturl()
            result["headers"] = dict(error.headers.items()) if error.headers else {}
            result["http_error"] = str(error)
        target = SNAP / f"{key}.html"
        target.write_bytes(body)
        result["snapshot"] = str(target.relative_to(ROOT))
        result["bytes"] = len(body)
        result["sha256"] = sha256(body).hexdigest()
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    results.append(result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

(ROOT / "fetch_manifest.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
