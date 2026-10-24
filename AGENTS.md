# AGENTS.md

## AI Attribution

**No AI attribution.** Do not append `Co-Authored-By: Claude …`, "Generated with
…", or any similar trailer to commit messages, PR bodies, or release notes. If
your tooling adds such a line by default, remove it before committing.

## This README shares three sections with the personal profile

`what we make`, `install` and `source` are duplicated, byte for byte, in
`magmacrunchmedia/magmacrunchmedia` at `README.md`, which is checked out in this
tree at `web\magmacrunchmedia`. GitHub profile READMEs cannot include a shared
file, so the only thing keeping them honest is updating both.

Check them with:

```bash
diff <(sed -n '/^<h3 align="left">what we make/,/^For source access/p' profile/README.md) \
     <(sed -n '/^<h3 align="left">what we make/,/^For source access/p' ../magmacrunchmedia/README.md)
```

The wording is deliberately correct on both pages, which is why the source
section says "the org's repositories" rather than "repositories here": the
personal account holds one public repository and the org holds the rest.

## The folder is not called `.github`

The repo is `magmacrunch-media/.github`; the checkout here is `web\org-profile`.
A directory beginning with a dot is invisible to a bash glob, so the tree sweeps
in `dev\CLAUDE.md` that iterate `web/*` would skip it while the `find -name .git`
sweep counted it. See that file for the full note.

<!-- shared-rules:start  Synced from magmacrunch-media/.github/agents-preamble.md. Do not edit here. -->
## House rules (shared)

Identical in every magmacrunch repo. The source is `agents-preamble.md` in the
public `.github` repo, and `agents-sync.py` in dev-tree replaces whatever sits
between these markers, so **an edit made here is reverted rather than spread.**
Change the source and re-sync. The source is public so that a drift check can
read it from any repo, including the three that are public themselves.

The sections ABOVE this block are the repo's own, and they win. Where a repo
states a different rule with a reason, that reason is the one to follow. This
block is last on purpose: a reader meets what is specific to the repo before
what is true everywhere.

### Commits

- **Commit as yourself. Any member of the `magmacrunch-media` org is correct**,
  loosened from the owner account alone on 2026-10-16. On the shared dev box
  that is `magmacrunchmedia <magmacrunchmedia@gmail.com>`, set by a `gitdir`
  conditional include, so do NOT set `user.email` in a repo there; a local value
  silently defeats it. `dev\jamccoy\` commits as Jake McCoy, by the same rule.
  `dev-tree/identity-sweep.sh` checks this by asking GitHub which account a
  commit belongs to and whether it is in the org, so there is no list of names
  to keep current and nothing to add when somebody joins.
- **No AI attribution anywhere**: not in commit messages, PR bodies, release
  notes, comments or docs. No `Co-authored-by` for a model, no generated-with
  line, no robot emoji.
- Subject lines are sentence-case and imperative, with no `feat:` or `chore:`
  prefix.
- Say what you verified and how. A commit that claims a result names the command
  or the file that produced it.

### Text

- **Write LF.** `core.autocrlf` is true on the dev box and does not normalise
  these repos on the way in, so a CRLF file stages as a whole-file rewrite that
  buries the real edit. The check is `git diff --numstat` against
  `git diff --numstat --ignore-cr-at-eol`: if they disagree, the CR is the diff.
- **Go easy on em dashes.** The objection is to them used heavily in prose, not
  to the character. CI counts them on added lines and warns; it does not block.
- Never convert the line endings of a third-party export or fixture. Those are
  pinned with `.gitattributes` on purpose.

### If this repo is checked out under `C:\magma\dev`

Several agent sessions share that one working tree and one index, so files you
never touched will already be staged, and they are somebody else's work in
flight. **Commit by pathspec**: `git commit -F <msgfile> -- <paths>`. Never
`git add -A`, `git commit -a`, `git reset --hard` or `git checkout -- .`.

A repo cloned outside that tree has one writer and none of this applies.

### Claims

**Cite the file or the command, not your reasoning.** Every wrong statement this
convention exists to prevent came from one of three things, each of which has
cost real time here:

- asserting from the shape of the code instead of reading it,
- reading a number correctly and reporting it without its denominator,
- reading back a write and believing the answer. An API can report success and
  show you nothing, or resolve an object that is attached to nothing.

So: measure, name the source, date anything that will go stale, and say plainly
what you did not check. A check that passes by finding nothing is the failure
this whole tree is organised against, which is why every checker here prints how
much it examined and fails when that comes back impossible.

### Design and intent

LLM tools are used here to free attention for design, not to skip it. The full
statement is `llm-tools.md` in the `company` repo.

- **Fun is the deliverable.** Whether something plays well, looks good and
  feels natural is the point, and that is a person's judgement. Bring
  decisions about feel, pacing, look and difficulty back to a person rather
  than settling them with a default.
- **Not a shortcut.** A smaller thing that has been tuned beats a complete one
  nobody has played. Do not trade care for speed.
- **Make our own software.** Prefer building the engine, editor or helper over
  pulling in a dependency when it shapes the work. Generated characters, art
  and levels are placeholders: the aim is our own editors, so a person can
  make and tweak them by hand.
- **No house AI style.** Avoid the stock patterns of generated work: centred
  hero, card grid, gradient buttons and emoji headings in layout; "not just X",
  buzzwords, filler and tidy triplets in writing. `tells-status.py` flags some
  of the writing ones. Match the project's own look and the author's voice.
- **Learn the languages we lean on.** C, JavaScript/TypeScript and Python are
  worth understanding, not only generating. When asked about non-obvious code,
  explain it rather than just swapping it out.
<!-- shared-rules:end -->
