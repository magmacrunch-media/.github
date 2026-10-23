#!/usr/bin/env python3
"""Count the habits that make generated text read as generated, in text being
ADDED to this tree. It REPORTS and passes; it does not refuse.

    python tells-status.py                  # what is staged (hook mode)
    python tells-status.py --range A..B     # the lines a commit range added
    python tells-status.py --tree DIR...    # every tracked line under DIR, an audit

em-dash-status.sh runs this after itself, so every repo whose pre-commit
runs that runs this too, with no hook of its own to install or keep current.
Literal em dashes are that script's; this one leaves them alone.

WHAT IT READS: only what somebody using the thing reads. Visible HTML text
and the attributes a person sees (title, alt, aria-label, placeholder,
content, value); string literals in JS/TS and Python, not their comments or
docstrings; string values in JSON; and READMEs, outside code. A comment is
for the next developer, and the published site strips them anyway
(scripts/build-site.mjs), so flagging them would be noise about text nobody
outside sees. Which part of a line is a string is decided from the whole
file, not the diff, so a line in the middle of a multi-line template literal
is read as the string it is.

A repo says what is its own content, not this check's business, in a
`.tells-ignore` at its root: one path prefix (ending /) or glob per line.
The website lists its archive, press, music and generated files there. Test
files, vendored and built code, and dev-only *-test.html pages are skipped
everywhere.

WHAT IT LOOKS FOR, each a category in the report:
    buzzword     marketing vocabulary: seamless, robust, leverage, delve...
    not-just     "not just X", "more than just", "isn't just"
    filler       stock openers: "it's worth noting", "let's dive in"...
    emoji        colour pictographs, which plain labels or text symbols beat
    entity-dash  &mdash; used in prose, which the em-dash check cannot see.
                 A lone &mdash; standing for an empty value is not flagged.

It is ADVISORY: a list for a person to read, because whether "robust" is a
tell or the right word is a judgement no pattern can make. Existing lines are
never touched or reported outside --tree.

EXIT CODES
    0  it ran; findings, if any, are above
    2  it could not run, or git reports added lines in files it should have
       read and it found none: it did not read the diff, so the silence means
       nothing. Same rule as em-dash-status.sh.

This file is pure ASCII: every non-ASCII pattern is written as an escape, so
it cannot flag itself and nothing can mangle it in transit.
"""
import html, io, json, os, re, subprocess, sys, tokenize

# ---------------------------------------------------------------- patterns --

BUZZWORDS = [
    "seamless", "seamlessly", "robust", "comprehensive", "leverage", "leverages",
    "leveraging", "delve", "delves", "delving", "elevate", "elevates",
    "elevated", "effortless", "effortlessly", "empower", "empowers",
    "empowering", "game-changer", "game changer", "game-changing",
    "cutting-edge", "state-of-the-art", "tapestry", "testament to",
    "immersive", "meticulous", "meticulously", "vibrant", "nestled",
    "embark", "embarks", "realm", "bustling", "unleash", "unleashes",
    "supercharge", "revolutionize", "revolutionizes", "revolutionary",
    "next-level", "world-class", "boasts", "elevating", "harness the",
    "in today's", "whether you're", "look no further",
    "dive deep", "deep dive", "unlock the", "unlock your", "curated",
    "transformative", "synergy", "holistic", "paradigm",
]
CATEGORIES = [
    ("buzzword", re.compile(r"(?<![\w-])(" + "|".join(re.escape(w) for w in BUZZWORDS)
                            + r")(?![\w-])", re.I)),
    ("not-just", re.compile(r"\b(not just|more than just|isn't just|aren't just|"
                            r"is not just|are not just|it's not about)\b", re.I)),
    ("filler", re.compile(r"\b(it's worth noting|it is worth noting|let's dive|"
                          r"say goodbye to|imagine a world|in conclusion|"
                          r"without further ado|buckle up|look no further|"
                          r"rest assured|at the end of the day)\b", re.I)),
    # The playing-card block, U+1F0A0 to U+1F0FF, is text by default: a card
    # game's back or face is a card, not an emoji. Only its joker, U+1F0CF,
    # draws in colour, so it alone is kept.
    ("emoji", re.compile("[" + chr(0x1F000) + "-" + chr(0x1F09F) + chr(0x1F0CF) + chr(0x1F100) + "-"
                         + chr(0x1FAFF) + "]|[" + chr(0x2600) + "-"
                         + chr(0x27BF) + "]" + chr(0xFE0F) + "|["
                         + "".join(map(chr, (0x2705, 0x2728, 0x274C, 0x2757, 0x2753, 0x2B50))) + "]")),
    # Prose, not a placeholder: a word or space on both sides.
    ("entity-dash", re.compile(r"(?<=[\w\s,.;:)])\s*&(?:mdash|#8212|#x2014);\s*(?=[\w(<])", re.I)),
]

# ---------------------------------------------------- what a file shows --

CODE_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
HTML_EXT = {".html", ".htm"}
SKIP_DIR = re.compile(r"(^|/)(node_modules|vendor|dist|build|third_party|"
                      r"tests?|__tests__|fixtures|admin)/")


TEST_FILE = re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$|^test_.*\.py$|_test\.py$|-test\.html$)")
IGNORE = []  # from .tells-ignore at the repo root, read in main()


def load_ignore():
    """`.tells-ignore` at the repo root: one path prefix or glob per line, #
    for comments. For a repo's own content, which is not this check's
    business: a label's published papers, an archive of other people's
    words, a generated index that repeats every page."""
    try:
        with open(".tells-ignore", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    except OSError:
        return []


def ignored(path):
    import fnmatch
    for pat in IGNORE:
        if pat.endswith("/") and path.startswith(pat):
            return True
        if fnmatch.fnmatch(path, pat) or path == pat:
            return True
    return False


def wanted(path):
    """The files this reads at all. Everything else is reported as unchecked."""
    base = path.rsplit("/", 1)[-1]
    if base == "tells-status.py":
        return False  # its own word lists are every tell it knows
    if (SKIP_DIR.search(path) or ".min." in base or TEST_FILE.search(base)
            or ignored(path)):
        return False
    ext = os.path.splitext(base)[1].lower()
    if ext in CODE_EXT | HTML_EXT | {".py", ".webmanifest"}:
        return True
    if ext == ".json":
        return not base.endswith(("-lock.json", "package.json", "tsconfig.json"))
    if not (base.lower().startswith("readme") and ext in {".md", ".txt", ""}):
        return False
    # A README is read where it is published: a repo's landing page, or a
    # package's PyPI or npm page. One inside a copied folder is never served.
    folder = path.rsplit("/", 1)[0] if "/" in path else ""
    return folder == "" or any(os.path.exists(os.path.join(folder, m))
                               for m in ("pyproject.toml", "package.json"))


def js_visible(text):
    """Per line, the characters inside JS string and template literals only.

    A small scanner over the whole file, so comment and string state carries
    across lines. It follows ${...} inside template literals, templates nested
    in them included, and skips regex literals by the usual heuristic. Where
    it still guesses wrong, the cost is a line read wrongly in a report that
    refuses nobody."""
    out = [[] for _ in range(text.count("\n") + 1)]
    line, i, n, state = 0, 0, len(text), "code"
    quote = None
    last = ""  # the last significant code character, to tell a regex from division
    tpl = []   # brace depth inside each open ${...}, innermost last
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "\n":
            line += 1
            if state == "line":
                state = "code"
            i += 1
            continue
        if state == "code":
            if c == "/" and nxt == "/":
                state = "line"; i += 2; continue
            if c == "/" and nxt == "*":
                state = "block"; i += 2; continue
            if c == "/" and (last == "" or last in "(,=:[!&|?{};+-*%<>~^"):
                # A regex literal: skip to its closing slash, minding escapes
                # and character classes, so a quote inside it is not a string.
                j, cls = i + 1, False
                while j < n and text[j] != "\n":
                    if text[j] == "\\":
                        j += 2; continue
                    if text[j] == "[":
                        cls = True
                    elif text[j] == "]":
                        cls = False
                    elif text[j] == "/" and not cls:
                        break
                    j += 1
                i, last = j + 1, "/"
                continue
            if tpl and c == "}":
                if tpl[-1] == 0:
                    tpl.pop()
                    state, quote = "str", "`"
                    i += 1
                    continue
                tpl[-1] -= 1
            elif tpl and c == "{":
                tpl[-1] += 1
            if c in "'\"`":
                state, quote = "str", c
            elif not c.isspace():
                last = c
        elif state == "block":
            if c == "*" and nxt == "/":
                state = "code"; i += 2; continue
        elif state == "str":
            if c == "\\":
                out[line].append(text[i:i + 2]); i += 2; continue
            if quote == "`" and c == "$" and nxt == "{":
                tpl.append(0)
                state, last = "code", "{"
                out[line].append(" ")
                i += 2
                continue
            if c == quote:
                state, last = "code", c
                out[line].append(" ")
            else:
                out[line].append(c)
        i += 1
    return ["".join(p) for p in out]


def py_visible(text):
    """Per line, Python string literals that are not docstrings."""
    lines = text.split("\n")
    out = [[] for _ in lines]
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return lines  # unparseable: read every line rather than none
    prev = tokenize.NEWLINE
    for t in toks:
        kinds = {tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)}
        docstring = t.type == tokenize.STRING and prev in (tokenize.NEWLINE, tokenize.INDENT,
                                                           tokenize.DEDENT, tokenize.NL)
        if t.type in kinds and not docstring:
            body = t.string.split("\n")
            for k, part in enumerate(body):
                if t.start[0] - 1 + k < len(out):
                    out[t.start[0] - 1 + k].append(part)
        if t.type not in (tokenize.COMMENT, tokenize.NL):
            prev = t.type
    return [" ".join(p) for p in out]


ATTR = re.compile(r"\b(?:title|alt|aria-label|placeholder|content|value)\s*=\s*"
                  r"(\"[^\"]*\"|'[^']*')", re.I)


def html_visible(text):
    """Per line, visible text and the attributes a person reads. Comments and
    style blocks go; script blocks are read as JS, strings only."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"<style\b.*?</style\s*>", blank, text, flags=re.S | re.I)
    lines = [""] * (text.count("\n") + 1)
    for m in re.finditer(r"(<script\b[^>]*>)(.*?)(</script\s*>)", text, flags=re.S | re.I):
        first = text.count("\n", 0, m.start(2))
        for k, s in enumerate(js_visible(m.group(2))):
            lines[first + k] += " " + s
        text = text[:m.start()] + blank(m) + text[m.end():]
    for k, raw in enumerate(text.split("\n")):
        attrs = " ".join(v[1:-1] for v in ATTR.findall(raw))
        words = re.sub(r"<[^>]*>", " ", raw)
        lines[k] += " " + attrs + " " + words
    return lines


def json_visible(text):
    return [" ".join(re.findall(r'"((?:\\.|[^"\\])*)"', l)) for l in text.split("\n")]


def md_visible(text):
    out, fence = [], False
    for l in text.split("\n"):
        if l.lstrip().startswith(("```", "~~~")):
            fence = not fence; out.append(""); continue
        out.append("" if fence else re.sub(r"`[^`]*`", " ", l))
    return out


def visible(path, text):
    ext = os.path.splitext(path)[1].lower()
    if ext in CODE_EXT:
        return js_visible(text)
    if ext in HTML_EXT:
        return html_visible(text)
    if ext == ".py":
        return py_visible(text)
    if ext in {".json", ".webmanifest"}:
        return json_visible(text)
    return md_visible(text)

# --------------------------------------------------------------- git side --


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True)
    if check and r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())
    return r.stdout.decode("utf-8", "replace")


def added_lines(mode, rng, paths):
    """{path: [line numbers added]} from a -U0 diff that ignores CR-only
    changes, so a renormalisation does not read as new text."""
    base = ["diff", "-U0", "--no-color", "--ignore-cr-at-eol", "--diff-filter=d"]
    args = base + ([rng] if mode == "range" else ["--cached"]) + ["--", *paths]
    added, path, ln = {}, None, 0
    for l in git(*args).split("\n"):
        if l.startswith("+++ "):
            path = l[6:] if l.startswith("+++ b/") else None
        elif l.startswith("@@ "):
            m = re.search(r"\+(\d+)", l)
            ln = int(m.group(1)) if m else 0
        elif l.startswith("+") and path:
            added.setdefault(path, []).append(ln)
            ln += 1
    return added


def blob(mode, rng, path):
    spec = (rng.split("..")[-1] or "HEAD") + ":" + path if mode == "range" else ":" + path
    r = subprocess.run(["git", "cat-file", "blob", spec], capture_output=True)
    return r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")


def scan(path, text, only=None):
    """Findings in one file: (line, category, match, line text)."""
    found = []
    raw = text.split("\n")
    for i, vis in enumerate(visible(path, text), start=1):
        if only is not None and i not in only:
            continue
        for cat, rx in CATEGORIES:
            # An emoji written as &#128218; draws the same as the character,
            # so decode entities for that check. Only for that one: the
            # entity-dash check needs to see &mdash; as written.
            for m in rx.finditer(html.unescape(vis) if cat == "emoji" else vis):
                src = raw[i - 1].strip() if i - 1 < len(raw) else vis
                found.append((i, cat, m.group(0).strip(), src))
    return found

# ---------------------------------------------------------------- self-test --

def self_test():
    """The cases that each fooled an earlier version. `--self-test` runs them."""
    tick = chr(96)
    cases = [
        # (path, text, line numbers that must be flagged, lines that must not)
        ("a.js", "// a robust comment\nconst s = 'robust';\n", {2}, {1}),
        ("a.js", "const r = /['\"]/g;\n// robust, in a comment after a regex\n", set(), {2}),
        ("a.js", "x = " + tick + "a ${n ? " + tick + "b" + tick + " : 'c'} d" + tick + ";\n"
                 "const w = winner; // robust\n", set(), {2}),
        ("a.js", "x = " + tick + "<p>one\nseamless two</p>" + tick + ";\n", {2}, set()),
        ("a.js", "y = a / b; z = 'robust';\n", {1}, set()),
        ("a.html", "<!-- robust -->\n<p>robust</p>\n<span>&mdash;</span>\n<p>a &mdash; b</p>\n",
         {2, 4}, {1, 3}),
        ("a.py", '"""A robust docstring."""\nx = "robust"  # robust\n', {2}, {1}),
        ("b.js", "a = '" + chr(0x1F0A0) + "';\nb = '" + chr(0x1F0CF) + "';\n", {2}, {1}),
        ("b.html", "<div>&#128218;</div>\n<div>&#x1F4DA;</div>\n<div>&#9654;</div>\n",
         {1, 2}, {3}),
    ]
    bad = 0
    for path, text, want, never in cases:
        got = {f[0] for f in scan(path, text)}
        if not want <= got or got & never:
            bad += 1
            print(f"SELF-TEST FAIL {path} {text[:50]!r}: flagged {sorted(got)}, "
                  f"wanted {sorted(want)}, never {sorted(never)}")
    print(f"self-test: {len(cases) - bad} of {len(cases)} cases pass")
    return 1 if bad else 0

# -------------------------------------------------------------------- main --


def main(argv):
    # A finding quotes the line, emoji included, and a Windows console is
    # cp1252: printing one raised, which a hook reads as a failed check.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="backslashreplace")
    mode, rng, trees = "staged", None, []
    it = iter(argv)
    for a in it:
        if a == "--range":
            mode, rng = "range", next(it, None)
        elif a == "--tree":
            mode = "tree"
            trees.extend(x for x in it)
        elif a == "--self-test":
            return self_test()
        elif a in ("-h", "--help"):
            print(__doc__); return 0
        else:
            print(f"tells-status: unknown argument {a!r}", file=sys.stderr); return 2
    if mode == "range" and not rng:
        print("tells-status: --range needs A..B", file=sys.stderr); return 2
    try:
        top = git("rev-parse", "--show-toplevel").strip()
    except (RuntimeError, FileNotFoundError):
        print("tells-status: not inside a git repository.", file=sys.stderr); return 2
    os.chdir(top)
    IGNORE[:] = load_ignore()

    if mode == "tree":
        files = [p for p in git("ls-files", "--", *(trees or ["."])).split("\n") if p]
        read = [p for p in files if wanted(p)]
        findings = []
        for p in read:
            try:
                text = open(p, encoding="utf-8", errors="replace").read().replace("\r\n", "\n")
            except OSError:
                continue
            findings += [(p, *f) for f in scan(p, text)]
        report(findings, f"{len(read)} tracked file(s) under {' '.join(trees) or '.'}",
               lines_seen=None, expected=None, unchecked=[])
        return 0

    what = f"range {rng}" if mode == "range" else "staged changes"
    names = (git("diff", "--name-only", "--diff-filter=d", rng) if mode == "range"
             else git("diff", "--cached", "--name-only", "--diff-filter=d"))
    changed = [p for p in names.split("\n") if p]
    read = [p for p in changed if wanted(p)]
    unchecked = [p for p in changed if not wanted(p)]
    added = added_lines(mode, rng, read) if read else {}
    seen = sum(len(v) for v in added.values())
    expected = 0
    if read:
        ns = (git("diff", "--numstat", "--ignore-cr-at-eol", rng, "--", *read) if mode == "range"
              else git("diff", "--cached", "--numstat", "--ignore-cr-at-eol", "--", *read))
        for l in ns.split("\n"):
            f = l.split("\t")
            if len(f) == 3 and f[0].isdigit():
                expected += int(f[0])
    findings = []
    for p, nums in added.items():
        findings += [(p, *f) for f in scan(p, blob(mode, rng, p), only=set(nums))]
    status = report(findings, f"{what}, across {len(read)} of {len(changed)} changed file(s)",
                    lines_seen=seen, expected=expected, unchecked=unchecked)
    return status


def report(findings, scope, lines_seen, expected, unchecked):
    for p, ln, cat, hit, src in findings:
        print(f"{p}:{ln}: [{cat}] {hit!s}  |  {src[:110]}")
    print()
    if lines_seen is None:
        print(f"Tells: read {scope}.")
    else:
        print(f"Tells: examined {lines_seen} added line(s) in {scope}.")
        if unchecked:
            shown = ", ".join(unchecked[:6]) + (f", and {len(unchecked) - 6} more" if len(unchecked) > 6 else "")
            print(f"Not text a reader sees, so unchecked ({len(unchecked)}): {shown}")
        if lines_seen == 0 and expected:
            print(f"\nTHIS CHECK DID NOT READ THE DIFF: git reports {expected} added line(s)"
                  " in the file(s) above and this found none.")
            return 2
    if findings:
        cats = {}
        for f in findings:
            cats[f[2]] = cats.get(f[2], 0) + 1
        print("WARNING: " + ", ".join(f"{n} {c}" for c, n in sorted(cats.items())) +
              ". Not a refusal: read each and keep the ones that are the right word.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
