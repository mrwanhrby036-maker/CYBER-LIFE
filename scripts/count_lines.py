#!/usr/bin/env python3
"""Count meaningful source lines per file and write docs/LINE_COUNT_REPORT.md."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTS = {".py", ".js", ".html", ".css", ".json", ".md", ".svg", ".sh", ".rules", ".example", ".txt", ".yml", ".yaml"}
SKIP_DIRS = {"node_modules", ".data", "__pycache__", ".pytest_cache", ".git", ".venv", "dist", "build", ".vercel"}
SKIP_FILES = {"package-lock.json"}


def count_file(path: Path) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return {"path": str(path.relative_to(ROOT)), "total": 0, "code": 0, "blank": 0, "comment": 0}
    total = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comment = 0
    suffix = path.suffix
    in_block = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if suffix == ".py":
            if s.startswith("#"):
                comment += 1
        elif suffix in {".js", ".css"}:
            if in_block:
                comment += 1
                if "*/" in s:
                    in_block = False
            elif s.startswith("/*"):
                comment += 1
                in_block = "*/" not in s
            elif s.startswith("//") or s.startswith("*"):
                comment += 1
        elif suffix == ".html":
            if s.startswith("<!--"):
                comment += 1
        elif suffix == ".md":
            if s.startswith("#"):
                comment += 1
    return {"path": str(path.relative_to(ROOT)), "total": total, "code": total - blank - comment, "blank": blank, "comment": comment}


def main() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES or path.suffix not in EXTS:
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            continue
        rows.append(count_file(path))
    totals = {k: sum(r[k] for r in rows) for k in ("total", "code", "blank", "comment")}
    by_top: dict[str, dict] = {}
    for r in rows:
        top = r["path"].split("/")[0]
        b = by_top.setdefault(top, {"files": 0, "total": 0, "code": 0})
        b["files"] += 1
        b["total"] += r["total"]
        b["code"] += r["code"]
    out = ROOT / "docs" / "LINE_COUNT_REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("# تقرير عدّ الأسطر الفعلي\n\n")
        f.write("تم توليده آليًا بواسطة `scripts/count_lines.py`. لا يشمل `node_modules` أو البيانات المحلية أو ملفات القفل.\n\n")
        f.write(f"- إجمالي الملفات المعدودة: **{len(rows)}**\n")
        f.write(f"- إجمالي الأسطر: **{totals['total']}**\n")
        f.write(f"- أسطر برمجية/محتوى (غير فارغة وغير تعليقات): **{totals['code']}**\n")
        f.write(f"- أسطر فارغة: {totals['blank']} — تعليقات/عناوين: {totals['comment']}\n\n")
        f.write("## حسب المجلد\n\n| المجلد | ملفات | إجمالي الأسطر | أسطر فعلية |\n|---|---:|---:|---:|\n")
        for top, b in sorted(by_top.items()):
            f.write(f"| `{top}` | {b['files']} | {b['total']} | {b['code']} |\n")
        f.write("\n## حسب الملف\n\n| الملف | إجمالي | فعلي | فارغ | تعليق |\n|---|---:|---:|---:|---:|\n")
        for r in rows:
            f.write(f"| `{r['path']}` | {r['total']} | {r['code']} | {r['blank']} | {r['comment']} |\n")
    (ROOT / "docs" / "line-count.json").write_text(json.dumps({"totals": totals, "by_top": by_top, "files": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(rows), **totals}, ensure_ascii=False))


if __name__ == "__main__":
    main()
