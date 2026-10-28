# syntax=docker/dockerfile:1
# Hermes Agent with Claude Code, so Hermes can delegate coding to Claude Code signed in with the owner's own Claude
# subscription (claude setup-token). Built from this folder as context.
#
# The git guard and its policy live in /etc/claude-code, the managed settings directory of Claude Code on Linux,
# owned by root: the agent (UID 10000) can read but not change or disable them. See docs/hermes-agent.md.

FROM nousresearch/hermes-agent:v0.21.6

ARG CLAUDE_CODE_VERSION=2.1.312
ARG GH_VERSION=2.103.3

# The base image starts as root: its init (s6) sets up the volume and drops to the hermes user
# hadolint ignore=DL3002,DL3008
RUN apt-get update \
 && apt-get install -y --no-install-recommends tmux \
 && rm -rf /var/lib/apt/lists/*

# The image's npm installs globals outside PATH, so /usr/local puts `claude` in /usr/local/bin. npm 12 blocks install
# scripts by default; Claude Code's postinstall puts its native binary in place
RUN npm install -g --prefix /usr/local --allow-scripts=@anthropic-ai/claude-code \
    "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
 && npm cache clean --force

# GitHub CLI from its release, checked against the published checksums
RUN cd /tmp \
 && curl -fsSLO "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz" \
 && curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_checksums.txt" \
    | grep "gh_${GH_VERSION}_linux_amd64.tar.gz" | sha256sum -c - \
 && tar -xzf "gh_${GH_VERSION}_linux_amd64.tar.gz" \
 && install -m 755 "gh_${GH_VERSION}_linux_amd64/bin/gh" /usr/local/bin/gh \
 && rm -rf /tmp/gh_*

COPY --chmod=644 claude/managed-settings.json /etc/claude-code/managed-settings.json
COPY --chmod=755 claude/hooks/git_guard.py /etc/claude-code/hooks/git_guard.py
COPY --chmod=644 claude/hooks/git_guard_test.py /tmp/git_guard_test.py

# A broken guard must never ship
RUN cp /tmp/git_guard_test.py /etc/claude-code/hooks/ \
 && /usr/bin/python3 /etc/claude-code/hooks/git_guard_test.py \
 && rm /etc/claude-code/hooks/git_guard_test.py /tmp/git_guard_test.py \
 && claude --version && gh --version && tmux -V
