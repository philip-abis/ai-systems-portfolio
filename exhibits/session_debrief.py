#!/usr/bin/env python3
"""Post-landing debrief — what must not be left behind when a session closes.

Every check here exists because the thing it looks for has gone wrong.
None of them are hypothetical:

  MACHINERY UNCOMMITTED   Skills, scripts, config and hooks belong in git;
                          source material and deliverables do not. A skill left
                          dirty is a skill that silently reverts on the next
                          machine.
  SKILL.md DRIFT          "If a skill's scripts change, SKILL.md changes in the
                          same session." Seven scripts were once added to a skill while its
                          SKILL.md still documented the superseded flow -- so the
                          skill, invoked fresh, would have reintroduced the exact
                          bugs that had just been removed.
  UNPUSHED                Work that exists only on this Mac is work that is one
                          disk failure from gone.
  ASSETS IN THE REPO      A repo was once found to be tracking 200 asset files
                          on GitHub -- scans and documents that had no business
                          being there. Recovery took a whole session. .gitignore
                          does nothing for files ALREADY tracked, so this looks
                          at what is actually tracked, not at what is ignored.
  STALE SKILL ZIPS        A skill edited but not repackaged means the copy in
                          Cowork is quietly older than the one in git.

TWO REPOS, NOT ONE. The debrief used to inspect only the repo you were standing
in, so a session that edited a global skill, a hook or ~/.claude/settings.json
got an ALL CLEAR while leaving that work uncommitted -- the global config is a
separate git repo and nothing in the project repo knows it is dirty. So this
checks the working repo AND ~/.claude, and reports them under separate headings:
when something is dirty, which repo it is dirty in decides where you commit.

Exit code is advisory only: 0 clean, 1 something needs attention. It never
blocks anything.

    python3 debrief.py [--repo PATH] [--no-global]
"""

import argparse
import os
import subprocess
import sys

GLOBAL_REPO = os.path.expanduser("~/.claude")

# Extensions that are source material or deliverables, never machinery.
ASSET_EXT = {
    ".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt", ".numbers",
    ".pages", ".key", ".jpg", ".jpeg", ".png", ".heic", ".gif", ".tiff",
    ".mp4", ".mov", ".m4a", ".mp3", ".wav", ".zip", ".csv",
}
# Paths that ARE machinery even though they may look like data.
MACHINERY_HINTS = (".claude/", "/scripts/", "SKILL.md", "CLAUDE.md",
                   ".sh", ".py", "settings.json", ".gitignore")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    # Trailing newline only. A full .strip() eats the leading space of the first
    # line of `status --porcelain` -- worktree-modified files are ` M path` --
    # and the l[3:] slice below then shears the first character off that path.
    # It cost a false SKILL.md DRIFT alarm: `.claude/...` became `claude/...`,
    # a second skill root that had scripts but no doc. The drift check is the one
    # this skill says to stop for, so a false positive in it is expensive.
    return r.stdout.rstrip("\n")


def is_machinery(path):
    return any(h in path for h in MACHINERY_HINTS)


def inspect(start):
    """Run every check against one repo. Returns None if `start` is not in a repo."""
    repo = git(start, "rev-parse", "--show-toplevel")
    if not repo:
        return None

    findings = []

    # --- 1. uncommitted machinery
    # --untracked-files=all matters: the default collapses a new directory to a
    # single `?? skills/postlanding/` line, which matches no machinery hint, so a
    # whole new skill reads as "non-machinery" and the repo reports clean.
    dirty = [l for l in git(repo, "status", "--porcelain",
                            "--untracked-files=all").splitlines() if l.strip()]
    dirty_paths = [l[3:].strip('"') for l in dirty]
    mach = [p for p in dirty_paths if is_machinery(p)]
    other = [p for p in dirty_paths if not is_machinery(p)]
    if mach:
        findings.append(("MACHINERY NOT COMMITTED",
                         "Skills, scripts, hooks and config belong in git.", mach))

    # --- 2. unpushed commits
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    upstream = git(repo, "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}")
    unpushed = []
    if upstream:
        unpushed = [l for l in git(repo, "log", "--oneline",
                                   f"{upstream}..HEAD").splitlines() if l]
        if unpushed:
            findings.append((f"NOT PUSHED ({branch} -> {upstream})",
                             "Work that exists only on this Mac.", unpushed))
    else:
        findings.append((f"NO UPSTREAM for {branch}",
                         "This branch has never been pushed.", [branch]))

    # --- 3. SKILL.md drift, over unpushed commits + working tree
    changed = set(dirty_paths)
    for c in unpushed:
        sha = c.split()[0]
        changed.update(git(repo, "show", "--name-only", "--format=", sha).splitlines())
    skills = {}
    for p in changed:
        if "/skills/" not in p:
            continue
        root = p.split("/skills/")[0] + "/skills/" + p.split("/skills/")[1].split("/")[0]
        skills.setdefault(root, set()).add(p)
    drift = []
    for root, paths in skills.items():
        touched_code = any("/scripts/" in p for p in paths)
        touched_doc = any(p.endswith("SKILL.md") for p in paths)
        if touched_code and not touched_doc:
            drift.append(f"{root} — scripts changed, SKILL.md did not")
    if drift:
        findings.append(("SKILL.md DRIFT",
                         "A skill whose docs lag its code reintroduces fixed bugs.",
                         drift))

    # --- 4. assets actually TRACKED by git (gitignore does not help these)
    tracked = git(repo, "ls-files").splitlines()
    assets = [p for p in tracked
              if os.path.splitext(p)[1].lower() in ASSET_EXT and not is_machinery(p)]
    if assets:
        findings.append(("ASSETS TRACKED IN GIT",
                         "Source material and deliverables do not belong in the repo. "
                         "Untracking needs `git rm --cached` — .gitignore alone will not do it.",
                         assets[:15] + ([f"...and {len(assets)-15} more"] if len(assets) > 15 else [])))

    # --- 5. skill zips older than their SKILL.md
    stale = []
    archives = os.path.expanduser("~/Developer/_archives")
    for dirpath, dirnames, filenames in os.walk(repo):
        if "SKILL.md" in filenames and "/skills/" in dirpath + "/":
            name = os.path.basename(dirpath)
            z = os.path.join(archives, f"{name}.zip")
            if os.path.exists(z):
                if os.path.getmtime(os.path.join(dirpath, "SKILL.md")) > os.path.getmtime(z):
                    stale.append(f"{name}.zip is older than its SKILL.md — repackage")
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
    if stale:
        findings.append(("SKILL PACKAGE STALE",
                         "The copy in Cowork is older than the copy in git.", stale))

    return {"repo": repo, "branch": branch, "upstream": upstream,
            "findings": findings, "other": other}


def report(label, result):
    """Print one repo's section. Returns True if it was clean."""
    print(f"── {label}: {result['repo']}")
    print(f"   branch {result['branch']}" +
          (f" -> {result['upstream']}" if result["upstream"] else " (no upstream)"))
    if result["other"]:
        print(f"   {len(result['other'])} non-machinery file(s) uncommitted — "
              f"deliverables/material, left alone by design")
    print()
    if not result["findings"]:
        print("   clean — machinery committed and pushed, docs in step, no assets tracked.")
        print()
        return True
    for title, why, items in result["findings"]:
        print(f"   [!] {title}")
        print(f"       {why}")
        for i in items:
            print(f"         - {i}")
        print()
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getcwd(),
                    help="the working repo to inspect (default: cwd)")
    ap.add_argument("--no-global", action="store_true",
                    help="skip the ~/.claude global-config repo")
    args = ap.parse_args()

    work = inspect(args.repo)
    glob = None if args.no_global else inspect(GLOBAL_REPO)
    # Standing inside ~/.claude itself: one repo, not two. Label it for what it is.
    same = bool(glob and work and glob["repo"] == work["repo"])
    work_label = "GLOBAL CONFIG" if same else "WORKING REPO"
    if same:
        glob = None

    if work is None and (args.no_global or glob is None):
        print("post-landing: not a git repository — nothing to check.")
        return 0

    print("Post-landing debrief")
    print()

    clean = True
    if work is None:
        print("── WORKING REPO: not a git repository — nothing to check there.")
        print()
    else:
        clean &= report(work_label, work)

    if not args.no_global and not same:
        if glob is None:
            print("── GLOBAL CONFIG: ~/.claude is not a git repository — global skills, "
                  "hooks and settings.json are backed up nowhere.")
            print()
            clean = False
        else:
            clean &= report("GLOBAL CONFIG", glob)

    if clean:
        print("  ALL CLEAR — both repos clean. Safe to close.")
        return 0
    print("  Commit in the repo the finding is listed under — the two have "
          "separate remotes and a commit in one does not carry the other.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
