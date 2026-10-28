#!/usr/bin/env python3
"""Claude Code PreToolUse hook: keeps an unattended agent to a safe subset of git and gh.

Installed as managed policy (/etc/claude-code, owned by root), so the agent cannot change or disable it. It is a
guard rail, not the security boundary: that is GitHub (ruleset on main, a bot account that cannot merge). The hook
stops the agent from even trying, and explains why, so it can take the allowed route.

Rules:
  git push        only to branches named hermes/<name>, explicitly; no force, delete, mirror, all, tags, no-verify
  git             no -c, no config writes, no remote changes, no history rewriting or destructive resets
  gh              allowlist: pull requests (create, view, list, diff, checks, comment), issues, repo view/clone
  Edit/Write      not in .github/workflows/, .git/ or the managed policy directory

Exit code 2 blocks the tool call and shows stderr to the agent; exit code 0 leaves the decision to the normal flow.
"""

import json
import re
import shlex
import sys

BRANCH_PREFIX = "hermes/"

GIT_DENIED_SUBCOMMANDS = {
    "filter-branch": "rewrites history",
    "filter-repo": "rewrites history",
    "rebase": "rewrites history; merge main into the branch instead",
    "update-ref": "moves refs directly",
    "replace": "rewrites objects",
    "reflog": "edits the safety net of lost commits",
    "gc": "prunes objects",
    "prune": "prunes objects",
    "remote": None,  # read-only forms allowed below
    "config": None,  # read-only forms allowed below
    "reset": None,  # --hard denied below
    "clean": "deletes untracked files",
    "branch": None,  # force delete denied below
    "push": None,  # checked below
    "submodule": "changes repository structure",
    "worktree": None,  # list allowed below
    "credential": "touches stored credentials",
    "send-email": "sends mail",
}

GH_ALLOWED = {
    ("pr", "create"), ("pr", "view"), ("pr", "list"), ("pr", "diff"), ("pr", "checks"), ("pr", "status"),
    ("pr", "comment"), ("pr", "checkout"),
    ("issue", "view"), ("issue", "list"), ("issue", "create"), ("issue", "comment"),
    ("repo", "view"), ("repo", "clone"),
    ("auth", "status"),
    ("run", "list"), ("run", "view"),
}

PROTECTED_PATH_PARTS = ("/.github/workflows/", "/.git/", "/etc/claude-code/")


def deny(reason: str) -> None:
    print(f"Blocked by the git guard: {reason}", file=sys.stderr)
    sys.exit(2)


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands (tokens), roughly as a shell would."""
    # Command substitutions and subshells are checked as commands of their own
    command = re.sub(r"\$\(|`|\(|\)", " ; ", command)
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        deny("could not parse the command (unbalanced quotes)")
    result, current = [], []
    for token in tokens:
        if token and set(token) <= set(";&|<>"):
            if current:
                result.append(current)
            current = []
        else:
            current.append(token)
    if current:
        result.append(current)
    return result


def strip_launchers(tokens: list[str]) -> list[str]:
    """Drop variable assignments and launchers such as env, sudo, nohup, timeout in front of the command."""
    launchers = {"env", "sudo", "command", "exec", "nohup", "nice", "time", "timeout", "stdbuf", "xargs"}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
            i += 1
        elif token.rsplit("/", 1)[-1] in launchers:
            i += 1
            # options and the duration of timeout
            while i < len(tokens) and (tokens[i].startswith("-") or re.match(r"^\d+[smhd]?$", tokens[i])):
                i += 1
        else:
            break
    return tokens[i:]


def check_git(args: list[str]) -> None:
    # Global options before the subcommand
    i = 0
    while i < len(args) and args[i].startswith("-"):
        option = args[i]
        if option == "-c" or option.startswith("-c") or option.startswith("--config-env"):
            deny("`git -c` can change hooks and credentials for one command; it is not allowed")
        if option in ("-C", "--git-dir", "--work-tree", "--namespace"):
            i += 2
            continue
        i += 1
    if i >= len(args):
        return
    sub, rest = args[i], args[i + 1:]

    if sub in GIT_DENIED_SUBCOMMANDS and GIT_DENIED_SUBCOMMANDS[sub]:
        deny(f"`git {sub}` {GIT_DENIED_SUBCOMMANDS[sub]}")
    if sub == "config":
        if not any(a in ("--get", "--get-all", "--get-regexp", "--list", "-l", "--show-origin") for a in rest):
            deny("`git config` may only read (--get, --list); identity and settings are fixed")
    if sub == "remote":
        if rest and rest[0] not in ("-v", "--verbose", "show", "get-url"):
            deny("remotes cannot be added or changed")
    if sub == "worktree" and rest and rest[0] != "list":
        deny("worktrees cannot be created or removed")
    if sub == "reset" and any(a in ("--hard", "--merge", "--keep") for a in rest):
        deny("`git reset --hard` discards work; use `git stash` or a new commit instead")
    if sub == "branch" and any(a in ("-D", "--delete", "-d", "-M", "--force", "-f") for a in rest):
        deny("branches cannot be deleted, renamed or overwritten")
    if sub in ("checkout", "switch", "restore") and any(a in ("-f", "--force", "-B", "-C") for a in rest):
        deny(f"`git {sub}` with force discards work")
    if sub == "commit" and any(a in ("--no-verify", "-n", "--amend") for a in rest):
        deny("commits cannot skip hooks or amend existing commits")
    if sub == "push":
        check_push(rest)


def check_push(rest: list[str]) -> None:
    forbidden = {
        "--force": "force push", "-f": "force push", "--force-with-lease": "force push",
        "--force-if-includes": "force push", "--mirror": "mirror push", "--all": "push of all branches",
        "--tags": "push of tags", "--follow-tags": "push of tags", "--delete": "deleting remote branches",
        "-d": "deleting remote branches", "--prune": "deleting remote branches", "--no-verify": "skipping hooks",
        "--receive-pack": "custom receive-pack", "--exec": "custom receive-pack", "--repo": "another repository",
    }
    positional = []
    for arg in rest:
        if arg.startswith("-"):
            name = arg.split("=", 1)[0]
            if name in forbidden or arg.startswith("--force"):
                deny(f"{forbidden.get(name, 'force push')} is not allowed")
            continue
        positional.append(arg)
    if len(positional) < 2:
        deny(f"push needs an explicit remote and branch, e.g. `git push -u origin {BRANCH_PREFIX}<name>`")
    remote, refspecs = positional[0], positional[1:]
    if remote != "origin":
        deny("only the remote `origin` may be pushed to")
    for refspec in refspecs:
        if refspec.startswith("+"):
            deny("force push (+refspec) is not allowed")
        source, _, target = refspec.partition(":")
        target = target or source
        if not source:
            deny("deleting remote branches is not allowed")
        target = target.removeprefix("refs/heads/")
        if not target.startswith(BRANCH_PREFIX) or len(target) == len(BRANCH_PREFIX):
            deny(f"push only to branches named `{BRANCH_PREFIX}<name>`, not `{target}`; main changes by pull request")


def check_gh(args: list[str]) -> None:
    words = [a for a in args if not a.startswith("-")]
    if len(words) < 2 or (words[0], words[1]) not in GH_ALLOWED:
        allowed = ", ".join(f"gh {a} {b}" for a, b in sorted(GH_ALLOWED))
        deny(f"`gh {' '.join(words[:2])}` is not allowed. Allowed: {allowed}")


def check_bash(command: str) -> None:
    if re.search(r"api\.github\.com|/repos/[^/\s]+/[^/\s]+/(pulls/\d+/merge|merges)", command):
        deny("direct calls to the GitHub API are not allowed; use the allowed gh commands")
    for tokens in segments(command):
        tokens = strip_launchers(tokens)
        if not tokens:
            continue
        program = tokens[0].rsplit("/", 1)[-1]
        if program in ("bash", "sh", "zsh", "dash") and "-c" in tokens[1:]:
            payload = tokens[tokens.index("-c") + 1] if tokens.index("-c") + 1 < len(tokens) else ""
            check_bash(payload)
        elif program == "git":
            check_git(tokens[1:])
        elif program == "gh":
            check_gh(tokens[1:])


def check_path(path: str) -> None:
    normalized = path if path.startswith("/") else "/" + path.removeprefix("./")
    for part in PROTECTED_PATH_PARTS:
        if part in normalized or normalized.endswith(part.rstrip("/")):
            deny(f"files under {part.strip('/')} cannot be edited")


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        deny("unreadable hook input")
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    if tool == "Bash":
        check_bash(tool_input.get("command", ""))
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        check_path(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    sys.exit(0)


if __name__ == "__main__":
    main()
