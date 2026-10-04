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
