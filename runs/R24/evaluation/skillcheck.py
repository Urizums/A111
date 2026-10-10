#!/usr/bin/env python3
"""Small structural check for a portable Skill; does not grade prose or behavior."""
from __future__ import annotations
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FIELD = re.compile(r"^([A-Za-z][\w-]*):\s*(.*?)\s*$", re.M)


def check(root: Path) -> dict:
    issues=[]
    root=root.resolve()
    if not root.is_dir():
        return {"passed":False,"errors":["not a directory"],"markdown_files":0,"links_checked":0}
    docs=list(root.rglob("*.md"))
    docs.sort()
    entry=root/"SKILL.md"
    if not entry.is_file():
        issues.append("missing SKILL.md")
    links=0
    for file in docs:
        try:
            text=file.read_text(encoding="utf-8",errors="strict")
        except (UnicodeError,OSError) as e:
            issues.append(f"cannot read UTF-8: {file.relative_to(root)}: {e}")
            continue
        if "\ufffd" in text:
            issues.append(f"replacement character: {file.relative_to(root)}")
        if file==entry:
            header=re.match(r"\A---\s*\n(.*?)\n---\s*\n",text,re.S)
            if not header:
                issues.append("SKILL.md missing YAML frontmatter")
            else:
                fields=dict(FIELD.findall(header.group(1)))
                for key in ("name","description"):
                    if not fields.get(key):
                        issues.append(f"SKILL.md missing nonempty {key}")
        for match in LINK.finditer(text):
            url=match.group(1).strip().split("#",1)[0]
            if not url or re.match(r"^[a-z][a-z0-9+.-]*:",url,re.I):
                continue
            links+=1
            target=(file.parent/url).resolve()
            if not target.is_relative_to(root):
                issues.append(f"link leaves Skill package: {file.relative_to(root)} -> {url}")
            elif not target.is_file():
                issues.append(f"missing reference: {file.relative_to(root)} -> {url}")
    return {"schema":"forge-r24-skill-structure/1","passed":not issues,
            "markdown_files":len(docs),"links_checked":links,"errors":issues,
            "scope":"metadata, UTF-8 and reference integrity; no content quality or Agent behavior verdict"}


def selftest() -> dict:
    results=[]
    def add(label,ok):results.append({"name":label,"passed":bool(ok)})
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/"skill"; (root/"references").mkdir(parents=True)
        entry=root/"SKILL.md"
        entry.write_text("---\nname: test-flow\ndescription: A short useful method\n---\nRead [reference](references/method.md).\n",encoding="utf-8")
        linked=root/"references/method.md";linked.write_text("# Methods\n",encoding="utf-8")
        add("minimal entry with link accepted",check(root)["passed"])
        linked.unlink();add("broken reference rejected",not check(root)["passed"])
        linked.write_text("# Methods\n",encoding="utf-8")
        entry.write_text("# no frontmatter\n",encoding="utf-8")
        add("missing metadata rejected",not check(root)["passed"])
        entry.write_text("---\nname: test-flow\ndescription: Valid\n---\n",encoding="utf-8")
        linked.write_bytes(b"\xff\xfe")
        add("invalid UTF-8 rejected",not check(root)["passed"])
        linked.write_text("# Methods\n",encoding="utf-8")
        entry.write_text("---\nname: test-flow\ndescription: Valid\n---\nRead [outside](../../other.md).\n",encoding="utf-8")
        add("escaped package reference rejected",not check(root)["passed"])
    return {"schema":"forge-r24-skillcheck-test/1","passed":all(r["passed"] for r in results),"checks":results,
            "note":"Structural tests only; no C13/C14 behavioral comparison"}


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path",nargs="?",type=Path)
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args(argv)
    if not args.selftest and args.path is None:
        parser.error("Provide a Skill directory or --selftest")
    result=selftest() if args.selftest else check(args.path)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["passed"] else 1

if __name__=="__main__":
    sys.exit(main())
