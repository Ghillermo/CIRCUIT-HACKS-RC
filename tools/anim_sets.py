"""The step-by-step animations (make_anim.py) in the manuals' two sets (the user, 2026-11-14: «integra las animaciones en la wiki y manual»).

    docs/manual/rc/anim/    the release candidate's set: the beta-only processes left out, and in every caption the beta's note cut (from
                            «Beta N only» / «Solo Beta N», or the parenthesis it opens, to the caption's end: make_anim puts the beta's
                            differences last);
    docs/manual/beta/anim/  the beta's set: every process as make_anim draws it (the beta's marks named as the current beta).

docset.build writes both (write_set) before the pages; make_guide.write (2026-11-15: the manual by views) puts each process once per chapter:
under the first of the chapter's features that it lists (feature_procs), or after the view's text when it lists none of them (view_procs), as
<img src="anim/anim-<id>-<lang>.svg"> (html_list; their CSS: make_manual.CSS).
Without a set (make_manual / make_guide run alone: the pages docset turns into redirects) nothing is drawn or linked.

    python tools/anim_sets.py           (checks: every process's view / features exist in the guide / the feature list; the RC captions)
"""
from __future__ import annotations
import copy
import html
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
MARK = re.compile(r"(?i)\s*\(?\*{0,2}(?:solo\s+beta\s+\d+\.\d+|beta\s+\d+\.\d+\s+only)\b.*$", re.S)
HEAD = {"es": "Paso a paso", "en": "Step by step"}
STEPS = {"es": "Los pasos en texto", "en": "The steps as text"}      # under each animation: its captions (search, copy, screen readers)
_CACHE = {}


def beta_name():
    import make_guide as G
    return getattr(G, "YNAME", G.YBETA)


def rc_text(text):
    """a caption of the RC's set: the beta's note (the last part of a caption, make_anim's rule) cut"""
    return MARK.sub("", text).rstrip()


def procs(variant):
    """the processes of a set ("rc" / "beta"), captions ready"""
    if variant in _CACHE: return _CACHE[variant]
    import make_anim as A
    import docset
    out = []
    for p in A.PROCESSES:
        if variant == "rc" and p.get("beta"): continue
        q = copy.deepcopy(p)
        for f in q["frames"]:
            for lang, t in f["caption"].items():
                f["caption"][lang] = rc_text(t) if variant == "rc" else docset.beta(t)
        if variant == "beta":                            # the beta set's own name in the title too («solo Alpha 7.16»), as in the captions
            q["mark"] = {lang: dict(A.MARK[lang], beta=docset.beta(A.MARK[lang]["beta"])) for lang in A.MARK}
        out.append(q)
    _CACHE[variant] = out
    return out


def write_set(out_dir, variant):
    """the set's SVGs into out_dir (anim-<id>-<lang>.svg; an old one no process makes is removed) -> the number written"""
    import make_anim as A
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = set()
    for p in procs(variant):
        for lang in ("en", "es"):
            name = A.file_name(p["id"], lang)
            path = out_dir / name
            svg = A.render(p, lang)
            if not path.exists() or path.read_text(encoding="utf-8") != svg:
                path.write_text(svg, encoding="utf-8", newline="\n")
            keep.add(name)
    for f in out_dir.glob("anim-*.svg"):
        if f.name not in keep: f.unlink()
    return len(keep)


def _title(p, lang):
    import make_anim as A
    m = p.get("mark", A.MARK)[lang]["beta"] if p.get("beta") else (f'{A.MARK[lang]["since"]} {p["since"]}' if p.get("since") else "")
    return p["title"][lang] + (f" · {m}" if m else "")


def _html(ps, lang):
    import make_anim as A
    if not ps: return ""
    figs = "".join(f'<figure class="anim"><img src="anim/{A.file_name(p["id"], lang)}" width="{A.W}" height="{A.H}" loading="lazy" '
                   f'decoding="async" alt="{html.escape(_title(p, lang), quote=True)}"></figure>'
                   f'<details class="anim-steps"><summary>{STEPS[lang]}</summary><ol>'
                   + "".join(f"<li>{html.escape(f['caption'][lang])}</li>" for f in p["frames"]) + "</ol></details>" for p in ps)
    return f'<div class="anims"><p class="anim-h"><strong>{HEAD[lang]}</strong></p>{figs}</div>'


def html_view(vid, lang, variant):
    """(make_guide) the animations of a view of the guide, or ""; variant = make_manual.SET"""
    if variant not in ("rc", "beta"): return ""
    return _html([p for p in procs(variant) if p["view"] == vid], lang)


def html_feature(sid, lang, variant):
    """(make_manual) the animations that list a feature section, or ""; variant = make_manual.SET"""
    if variant not in ("rc", "beta"): return ""
    return _html([p for p in procs(variant) if sid in p["features"]], lang)


def view_procs(vid, variant):
    """(make_guide, 2026-11-15: the manual by views) the processes of a view of the guide, or []"""
    if variant not in ("rc", "beta"): return []
    return [p for p in procs(variant) if p["view"] == vid]


def feature_procs(sid, variant):
    """(make_guide) the processes that list a feature section, or []"""
    if variant not in ("rc", "beta"): return []
    return [p for p in procs(variant) if sid in p["features"]]


def html_list(ps, lang):
    """the animations of a list of processes (the guide puts each one once per chapter), or \"\""""
    return _html(list(ps), lang)


def check():
    """-> problems: a process whose view is not a view of the guide or whose feature is not a section of the feature list; an RC caption
    that is empty or still names a beta"""
    import make_anim as A
    import make_guide as G
    import make_manual as M
    bad = []
    views = {v["id"] for v in G.data("es")[0]}
    M.use("es")
    secs = {s_["id"] for s_ in M.CUR["S"]}
    for p in A.PROCESSES:
        if p["view"] not in views: bad.append(f'{p["id"]}: view {p["view"]} is not in the guide')
        for s_ in p["features"]:
            if s_ not in secs: bad.append(f'{p["id"]}: feature {s_} is not in the feature list')
    for p in procs("rc"):
        for i, f in enumerate(p["frames"]):
            for lang, t in f["caption"].items():
                if not t.strip(): bad.append(f'{p["id"]} frame {i + 1} ({lang}): empty in the RC set')
                if re.search(r"(?i)\bbeta\b", t): bad.append(f'{p["id"]} frame {i + 1} ({lang}): names a beta in the RC set: {t[:80]}')
    return bad


if __name__ == "__main__":
    probs = check()
    for b in probs: print(b)
    print(len(procs("rc")), "processes in the RC set,", len(procs("beta")), "in the beta set;", len(probs), "problems")
    sys.exit(1 if probs else 0)
