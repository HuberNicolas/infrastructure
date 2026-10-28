"""Tests for git_guard.py; run during the image build, so a broken guard never ships."""

import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).with_name("git_guard.py")


def run(tool: str, **tool_input) -> int:
    event = {"tool_name": tool, "tool_input": tool_input}
    return subprocess.run([sys.executable, str(GUARD)], input=json.dumps(event), text=True, capture_output=True).returncode


ALLOWED = [
    "git status", "git diff --stat", "git log --oneline -5", "git add -A", "git commit -m 'Add login form'",
    "git checkout -b hermes/login-form", "git switch hermes/login-form", "git fetch origin", "git pull origin main",
    "git merge origin/main", "git push -u origin hermes/login-form", "git push origin HEAD:hermes/login-form",
    "git push origin hermes/a hermes/b", "git -C /opt/data/work/app status", "git config --get user.name",
    "git remote -v", "git stash", "git branch", "git branch hermes/x", "git worktree list",
    "gh pr create --fill --base main", "gh pr view 3", "gh pr list", "gh pr checks 3", "gh issue list",
    "gh repo clone HuberNicolas/genai-zurich-2027", "gh auth status",
    "npm test && git add . && git commit -m 'Fix test'", "cd app && git status | head",
    "echo 'git push origin main'", "python -m pytest",
    "git push -u origin hermes/smoke-test 2>&1", "git push origin hermes/x > /tmp/push.log 2>&1",
    "git status 2>/dev/null", "gh pr create --fill --base main 2>&1 | tail -5", "git push origin hermes/x &>/dev/null",
    "git log --oneline > /tmp/log.txt", "npm test 2>&1 | tail -20",
]

DENIED = [
    "git push", "git push origin main", "git push origin HEAD", "git push origin HEAD:main",
    "git push -u origin feature/x", "git push --force origin hermes/x", "git push -f origin hermes/x",
    "git push origin +hermes/x", "git push --force-with-lease origin hermes/x", "git push origin :hermes/x",
    "git push --delete origin hermes/x", "git push --mirror origin", "git push --all origin",
    "git push --tags origin", "git push upstream hermes/x", "git push origin hermes/",
    "git push --no-verify origin hermes/x", "git push origin refs/heads/main",
    "git -c core.hooksPath=/tmp push origin hermes/x", "git config user.email x@y", "git config --global a b",
    "git remote add evil https://example.com/r.git", "git remote set-url origin https://x",
    "git reset --hard HEAD~3", "git clean -fdx", "git branch -D hermes/x", "git branch -M main",
    "git rebase main", "git filter-branch --all", "git commit --amend -m x", "git commit --no-verify -m x",
    "git checkout -f main", "git reflog expire --all", "git gc --prune=now", "git worktree add ../x",
    "gh pr merge 3", "gh pr merge 3 --squash --admin", "gh api repos/HuberNicolas/x/pulls/3/merge -X PUT",
    "gh repo delete HuberNicolas/x", "gh repo edit --visibility public", "gh secret set X", "gh workflow run ci",
    "gh auth token", "gh release create v1", "gh ruleset list",
    "curl -X PUT https://api.github.com/repos/HuberNicolas/x/pulls/3/merge",
    "npm test && git push origin main", "cd app; git push --force origin hermes/x",
    "bash -c 'git push origin main'", "sh -c \"gh pr merge 1\"", "echo $(git push origin main)",
    "env GIT_TRACE=1 git push origin main", "timeout 30 git push origin main", "sudo git push origin main",
    "/usr/bin/git push origin main", "FOO=1 git push origin main", "git push 'origin' 'main",
    "git push origin main 2>&1", "git push origin main > /tmp/log 2>&1", "git push --force origin hermes/x 2>&1",
    "gh pr merge 1 2>&1 | tail", "git push origin hermes/x 2>&1; git push origin main",
]

PATHS_DENIED = [
    ".github/workflows/ci.yml", "/opt/data/work/app/.github/workflows/deploy.yml", ".git/hooks/pre-push",
    "/opt/data/work/app/.git/config", "/etc/claude-code/managed-settings.json",
]
PATHS_ALLOWED = ["src/app.py", "/opt/data/work/app/frontend/src/App.vue", ".github/ISSUE_TEMPLATE/bug.md", "README.md"]


def main() -> None:
    failures = []
    failures += [f"should allow: {c}" for c in ALLOWED if run("Bash", command=c) != 0]
    failures += [f"should deny:  {c}" for c in DENIED if run("Bash", command=c) != 2]
    failures += [f"should deny:  Write {p}" for p in PATHS_DENIED if run("Write", file_path=p) != 2]
    failures += [f"should allow: Write {p}" for p in PATHS_ALLOWED if run("Edit", file_path=p) != 0]
    total = len(ALLOWED) + len(DENIED) + len(PATHS_DENIED) + len(PATHS_ALLOWED)
    if failures:
        print("\n".join(failures))
        sys.exit(f"git guard: {len(failures)} of {total} checks failed")
    print(f"git guard: all {total} checks passed")


if __name__ == "__main__":
    main()
