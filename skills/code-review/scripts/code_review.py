#!/usr/bin/env python3
"""Line-annotated Git diff and GitHub Pull Request review helper and CI runner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import dataclasses
import datetime
import glob
import json
import os
import random
import re
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.request

CURRENT_GEMINI_MODELS: tuple[str, ...] = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)

IGNORE_PREFIXES: tuple[str, ...] = (
    "conductor/tracks/",
    ".agents/",
    ".github/workflows/",
    "docs/",
    "graphify-out/",
)

IGNORE_SUFFIXES: tuple[str, ...] = (
    ".md",
    ".lock",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".ico",
    ".gif",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
)

BOT_AUTHOR_LOGINS: frozenset[str] = frozenset(
    {"github-actions", "github-actions[bot]"}
)
GITHUB_API_BASE = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
FRONT_MATTER_PATTERN = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
MAX_PAYLOAD_CHARS = 120_000


class ReviewConfigError(RuntimeError):
    """Raised when required CLI flags, tokens, or repository metadata are missing."""


@dataclasses.dataclass(frozen=True)
class AnnotatedFileDiff:
    """New-file line numbers and annotated unified diff hunks for one modified file."""

    path: str
    valid_lines: frozenset[int]
    annotated_diff: str


@dataclasses.dataclass(frozen=True)
class OpenReviewThread:
    """Unresolved PR review thread posted before the latest commit."""

    thread_id: str
    comment_id: int | None
    path: str
    line: int | None
    original_line: int | None
    body: str
    diff_hunk: str = ""
    original_commit_oid: str = ""
    created_at: str = ""
    replies: tuple[str, ...] = ()


def get_env_var(*, name: str, default: str = "") -> str:
    """Return a stripped environment variable or its fallback default."""
    return os.environ.get(name, default).strip()


def resolve_github_token() -> str:
    """Resolve a GitHub token from GITHUB_TOKEN, GH_TOKEN, or `gh auth token`."""
    token = get_env_var(name="GITHUB_TOKEN") or get_env_var(name="GH_TOKEN")
    if token:
        return token
    try:
        output = subprocess.check_output(
            ["gh", "auth", "token"],
            stderr=subprocess.DEVNULL,
        )
        return output.decode("utf-8", errors="replace").strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise ReviewConfigError(
            "GITHUB_TOKEN is not set and `gh auth token` failed."
        ) from exc


def resolve_github_repo(*, explicit_repo: str = "") -> str:
    """Resolve `<owner>/<name>` from explicit input, REPO env, or `gh repo view`."""
    repo = explicit_repo.strip() or get_env_var(name="REPO")
    if repo:
        return repo
    try:
        output = subprocess.check_output(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            stderr=subprocess.DEVNULL,
        )
        resolved = output.decode("utf-8", errors="replace").strip()
        if resolved:
            return resolved
    except (subprocess.CalledProcessError, OSError) as exc:
        raise ReviewConfigError(
            "Pass --repo <owner/name> or set REPO when outside a GitHub checkout."
        ) from exc
    raise ReviewConfigError("Unable to resolve GitHub repository `<owner>/<name>`.")


def is_dependabot(*, author: str = "", branch: str = "") -> bool:
    """Report whether the PR author or branch belongs to Dependabot."""
    if author and "dependabot" in author.lower():
        return True
    return bool(branch and branch.lower().startswith("dependabot/"))


def should_skip_review(
    *,
    pr_number: str,
    pr_author: str = "",
    is_merged: str | bool = False,
    pr_info: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Check whether automated review should be skipped for merged or Dependabot PRs."""
    if str(is_merged).lower() in ("true", "1"):
        return True, f"PR #{pr_number} is already merged."
    if is_dependabot(author=pr_author):
        return True, f"PR #{pr_number} author is {pr_author} (Dependabot)."
    if pr_info is None:
        return False, ""
    if pr_info.get("merged") or pr_info.get("merged_at"):
        return True, f"PR #{pr_number} is already merged."
    author = (pr_info.get("user") or {}).get("login", "")
    branch = (pr_info.get("head") or {}).get("ref", "")
    if is_dependabot(author=author, branch=branch):
        return True, f"PR #{pr_number} is from Dependabot ({author or branch})."
    return False, ""


def _should_ignore_path(*, path: str) -> bool:
    return any(path.startswith(prefix) for prefix in IGNORE_PREFIXES) or any(
        path.endswith(suffix) for suffix in IGNORE_SUFFIXES
    )


def parse_and_annotate_diff(*, diff_text: str) -> dict[str, AnnotatedFileDiff]:
    """Parse unified diff text into per-file hunks annotated with right-side line numbers."""
    raw_files: dict[str, dict[str, Any]] = {}
    current_file: str | None = None
    skip_current = False
    new_line: int | None = None

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            b_path = parts[3] if len(parts) > 3 else ""
            current_file = b_path[2:] if b_path.startswith("b/") else b_path
            skip_current = not current_file or _should_ignore_path(path=current_file)
            if not skip_current and current_file:
                raw_files[current_file] = {"valid_lines": set(), "lines": []}
            new_line = None
            continue

        if skip_current or not current_file or current_file not in raw_files:
            continue

        hunk_match = HUNK_HEADER_PATTERN.match(raw_line)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            raw_files[current_file]["lines"].append(raw_line)
            continue

        if new_line is None:
            continue

        if raw_line.startswith("+"):
            raw_files[current_file]["valid_lines"].add(new_line)
            raw_files[current_file]["lines"].append(f"{new_line:4d}: + {raw_line[1:]}")
            new_line += 1
        elif raw_line.startswith(" "):
            raw_files[current_file]["valid_lines"].add(new_line)
            raw_files[current_file]["lines"].append(f"{new_line:4d}:   {raw_line[1:]}")
            new_line += 1
        elif raw_line.startswith("-"):
            raw_files[current_file]["lines"].append(f"    : - {raw_line[1:]}")
        else:
            raw_files[current_file]["lines"].append(raw_line)

    annotated: dict[str, AnnotatedFileDiff] = {}
    for fpath, data in raw_files.items():
        if data["valid_lines"]:
            annotated[fpath] = AnnotatedFileDiff(
                path=fpath,
                valid_lines=frozenset(data["valid_lines"]),
                annotated_diff="\n".join(data["lines"]),
            )
    return annotated


def load_styleguides(*, directories: Sequence[str]) -> str:
    """Load Markdown styleguides across candidate directories with YAML front matter stripped."""
    sections: list[str] = []
    seen_paths: set[str] = set()
    for directory in directories:
        if not directory or not os.path.isdir(directory):
            continue
        for path in sorted(glob.glob(os.path.join(directory, "*.md"))):
            real = os.path.realpath(path)
            if real in seen_paths:
                continue
            seen_paths.add(real)
            with open(path, encoding="utf-8") as handle:
                content = FRONT_MATTER_PATTERN.sub("", handle.read()).strip()
            if content:
                sections.append(f"## Rule: {os.path.basename(path)}\n\n{content}")
    if not sections:
        return ""
    return "# Workspace Rules & Styleguides\n\n" + "\n\n".join(sections)


def fetch_local_git_diff(
    *,
    staged: bool = False,
    commit: str = "",
    diff_range: str = "",
) -> str:
    """Collect unified diff output from the local Git repository."""
    if commit:
        cmd = ["git", "show", "--format=", "-U3", commit]
    elif diff_range:
        cmd = ["git", "diff", "-U3", diff_range]
    elif staged:
        cmd = ["git", "diff", "--cached", "-U3"]
    else:
        cmd = ["git", "diff", "-U3", "HEAD"]
    output = subprocess.check_output(cmd)
    return output.decode("utf-8", errors="replace")


def get_pr_info(*, repo: str, pr_number: str, github_token: str) -> dict[str, Any]:
    """Fetch Pull Request metadata from the GitHub REST API."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Marcel-Code-Review",
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pr_diff(
    *,
    repo: str,
    pr_number: str,
    github_token: str,
    base_sha: str = "",
    head_sha: str = "",
) -> str:
    """Fetch Pull Request unified diff from local Git history or the GitHub API."""
    if base_sha and head_sha:
        try:
            diff = subprocess.check_output(
                ["git", "diff", "-U3", f"{base_sha}...{head_sha}"],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="replace")
            if diff.strip():
                return diff
        except (subprocess.CalledProcessError, OSError):
            pass

    url = f"{GITHUB_API_BASE}/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Marcel-Code-Review",
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3.diff",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def github_graphql_request(
    *,
    github_token: str,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """Execute a GitHub GraphQL query or mutation and return its `data` mapping."""
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        GITHUB_GRAPHQL_URL,
        data=payload,
        headers={
            "User-Agent": "Marcel-Code-Review",
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    errors = body.get("errors")
    if errors:
        raise RuntimeError(f"GitHub GraphQL error: {errors}")
    return body.get("data") or {}


def _parse_iso_timestamp(*, value: str) -> datetime.datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed


def filter_open_prior_threads(
    *,
    threads_data: Sequence[dict[str, Any]],
    head_sha: str,
    latest_commit_date: str = "",
    bot_only: bool = True,
) -> list[OpenReviewThread]:
    """Filter review threads to unresolved comments created before the latest commit."""
    latest_dt = _parse_iso_timestamp(value=latest_commit_date)
    open_threads: list[OpenReviewThread] = []

    for thread in threads_data:
        if thread.get("isResolved"):
            continue
        comments = (thread.get("comments") or {}).get("nodes") or []
        if not comments:
            continue
        root = comments[0]
        author_login = ((root.get("author") or {}).get("login") or "").strip().lower()
        if bot_only and author_login not in BOT_AUTHOR_LOGINS:
            continue

        original_commit_oid = (
            (root.get("originalCommit") or {}).get("oid") or ""
        ).strip()
        created_at = (root.get("createdAt") or "").strip()
        created_dt = _parse_iso_timestamp(value=created_at)

        if head_sha and original_commit_oid and original_commit_oid == head_sha:
            continue
        if latest_dt is not None and created_dt is not None and created_dt >= latest_dt:
            continue
        if (
            bot_only
            and not original_commit_oid
            and (latest_dt is None or created_dt is None)
        ):
            continue

        replies: list[str] = []
        for reply_node in comments[1:]:
            reply_author = (
                (reply_node.get("author") or {}).get("login") or "unknown"
            ).strip()
            reply_body = (reply_node.get("body") or "").strip()
            if reply_body:
                replies.append(f"{reply_author}: {reply_body}")

        thread_id = (thread.get("id") or "").strip()
        path = (thread.get("path") or "").strip()
        body = (root.get("body") or "").strip()
        if not thread_id or not path or not body:
            continue

        open_threads.append(
            OpenReviewThread(
                thread_id=thread_id,
                comment_id=root.get("databaseId"),
                path=path,
                line=thread.get("line"),
                original_line=thread.get("originalLine"),
                body=body,
                diff_hunk=(root.get("diffHunk") or "").strip(),
                original_commit_oid=original_commit_oid,
                created_at=created_at,
                replies=tuple(replies),
            )
        )
    return open_threads


def fetch_open_threads(
    *,
    repo: str,
    pr_number: str,
    github_token: str,
    head_sha: str,
    bot_only: bool = True,
) -> list[OpenReviewThread]:
    """Fetch unresolved review threads on a Pull Request via GraphQL."""
    owner, name = repo.split("/", 1)
    query = """
    query($owner: String!, $name: String!, $prNumber: Int!) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $prNumber) {
          headRefOid
          commits(last: 1) {
            nodes {
              commit {
                oid
                committedDate
              }
            }
          }
          reviewThreads(first: 100) {
            nodes {
              id
              isResolved
              path
              line
              originalLine
              comments(first: 50) {
                nodes {
                  databaseId
                  author { login }
                  body
                  createdAt
                  originalCommit { oid }
                  diffHunk
                }
              }
            }
          }
        }
      }
    }
    """
    data = github_graphql_request(
        github_token=github_token,
        query=query,
        variables={"owner": owner, "name": name, "prNumber": int(pr_number)},
    )
    pr_data = (data.get("repository") or {}).get("pullRequest") or {}
    latest_oid = head_sha or (pr_data.get("headRefOid") or "").strip()
    latest_date = ""
    commit_nodes = (pr_data.get("commits") or {}).get("nodes") or []
    if commit_nodes:
        commit_obj = commit_nodes[-1].get("commit") or {}
        latest_date = (commit_obj.get("committedDate") or "").strip()
        if not latest_oid:
            latest_oid = (commit_obj.get("oid") or "").strip()
    threads_data = (pr_data.get("reviewThreads") or {}).get("nodes") or []
    return filter_open_prior_threads(
        threads_data=threads_data,
        head_sha=latest_oid,
        latest_commit_date=latest_date,
        bot_only=bot_only,
    )


def _read_file_at_head(
    *,
    path: str,
    head_sha: str,
    target_line: int | None = None,
) -> str | None:
    raw_content: str | None = None
    if head_sha:
        try:
            raw_content = subprocess.check_output(
                ["git", "show", f"{head_sha}:{path}"],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="replace")
        except (subprocess.CalledProcessError, OSError):
            raw_content = None
    if raw_content is None and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as handle:
                raw_content = handle.read()
        except OSError:
            raw_content = None
    if raw_content is None:
        return None

    numbered = [
        f"{idx:4d}: {line}" for idx, line in enumerate(raw_content.splitlines(), 1)
    ]
    if len(numbered) <= 250:
        return "\n".join(numbered)
    if target_line is not None and target_line > 100:
        start_idx = max(40, target_line - 45)
        end_idx = min(len(numbered), target_line + 45)
        parts = ["\n".join(numbered[:40])]
        if start_idx > 40:
            parts.append("... [lines omitted] ...")
        parts.append("\n".join(numbered[start_idx:end_idx]))
        if end_idx < len(numbered):
            parts.append("... [file truncated] ...")
        return "\n".join(parts)
    return "\n".join(numbered[:250]) + "\n... [file truncated] ..."


def _fetch_commit_file_diff(
    *,
    original_commit_oid: str,
    head_sha: str,
    path: str,
) -> str:
    if not original_commit_oid or not head_sha:
        return ""
    try:
        return (
            subprocess.check_output(
                ["git", "diff", "-U3", f"{original_commit_oid}..{head_sha}", "--", path],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8", errors="replace")
            .strip()
        )
    except (subprocess.CalledProcessError, OSError):
        return ""


def build_thread_context(
    *,
    thread: OpenReviewThread,
    head_sha: str,
    files_data: dict[str, AnnotatedFileDiff],
) -> dict[str, Any]:
    """Build structured validation context for a single open review thread."""
    focus_line = thread.line if thread.line is not None else thread.original_line
    file_diff = files_data.get(thread.path)
    return {
        "thread_id": thread.thread_id,
        "path": thread.path,
        "line": thread.line,
        "original_line": thread.original_line,
        "body": thread.body,
        "replies": list(thread.replies),
        "diff_hunk": thread.diff_hunk,
        "changes_since_comment": _fetch_commit_file_diff(
            original_commit_oid=thread.original_commit_oid,
            head_sha=head_sha,
            path=thread.path,
        ),
        "current_pr_diff": file_diff.annotated_diff if file_diff else "",
        "head_excerpt": _read_file_at_head(
            path=thread.path,
            head_sha=head_sha,
            target_line=focus_line,
        ),
    }


def reply_to_review_thread(
    *,
    github_token: str,
    thread_id: str,
    body: str,
) -> None:
    """Post a reply on a GitHub Pull Request review thread via GraphQL."""
    mutation = """
    mutation($threadId: ID!, $body: String!) {
      addPullRequestReviewThreadReply(
        input: {pullRequestReviewThreadId: $threadId, body: $body}
      ) {
        comment { id }
      }
    }
    """
    github_graphql_request(
        github_token=github_token,
        query=mutation,
        variables={"threadId": thread_id, "body": body},
    )


def resolve_review_thread(*, github_token: str, thread_id: str) -> None:
    """Mark a GitHub Pull Request review thread resolved via GraphQL."""
    mutation = """
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { id isResolved }
      }
    }
    """
    github_graphql_request(
        github_token=github_token,
        query=mutation,
        variables={"threadId": thread_id},
    )


def align_inline_comments(
    *,
    raw_comments: Sequence[dict[str, Any]],
    files_data: dict[str, AnnotatedFileDiff],
    base_summary: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Snap inline comment line numbers onto valid diff lines or fold into summary."""
    summary = base_summary
    valid_comments: list[dict[str, Any]] = []

    for item in raw_comments:
        fpath = str(item.get("path") or "").strip()
        line_val = item.get("line")
        body = str(item.get("body") or "").strip()
        if not fpath or line_val is None or not body:
            continue
        line = int(line_val)
        file_diff = files_data.get(fpath)
        if file_diff is None:
            summary += f"\n\n- **Note on `{fpath}`**: {body}"
            continue
        if line in file_diff.valid_lines:
            valid_comments.append(
                {"path": fpath, "line": line, "side": "RIGHT", "body": body}
            )
            continue
        closest = min(
            file_diff.valid_lines,
            key=lambda candidate: abs(candidate - line),
            default=None,
        )
        if closest is not None and abs(closest - line) <= 3:
            valid_comments.append(
                {"path": fpath, "line": int(closest), "side": "RIGHT", "body": body}
            )
        else:
            summary += f"\n\n- **Note on `{fpath}:{line}`**: {body}"

    return summary, valid_comments


def post_github_review(
    *,
    repo: str,
    pr_number: str,
    github_token: str,
    head_sha: str,
    summary: str,
    inline_comments: Sequence[dict[str, Any]],
    heading: str = "### Code Review",
) -> None:
    """Submit a formal GitHub Pull Request Review with 422 summary fallback."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "User-Agent": "Marcel-Code-Review",
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    review_body = summary if summary.startswith("### ") else f"{heading}\n\n{summary}"
    payload = {
        "commit_id": head_sha,
        "body": review_body,
        "event": "COMMENT",
        "comments": list(inline_comments),
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30):
            return
    except urllib.error.HTTPError as exc:
        if exc.code == 422 and inline_comments:
            fallback_body = review_body + "\n\n### Inline Findings\n"
            for comment in inline_comments:
                fallback_body += (
                    f"\n- **`{comment['path']}:{comment['line']}`**:\n{comment['body']}\n"
                )
            fallback_payload = {
                "commit_id": head_sha,
                "body": fallback_body,
                "event": "COMMENT",
                "comments": [],
            }
            retry_req = urllib.request.Request(
                url,
                data=json.dumps(fallback_payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(retry_req, timeout=30):
                return
        raise


def invoke_gemini_json(
    *,
    api_key: str,
    model: str,
    system_instructions: str,
    user_prompt: str,
    response_schema: dict[str, Any],
) -> dict[str, Any]:
    """Call the Gemini API with structured JSON output, retries, and model fallback."""
    models_to_try = [model] + [m for m in CURRENT_GEMINI_MODELS if m != model]
    req_body = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instructions}]},
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        },
    }
    data_bytes = json.dumps(req_body).encode("utf-8")
    last_error = "Unknown error"

    for candidate in models_to_try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{candidate}:generateContent?key={api_key}"
        )
        for attempt in range(3):
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                candidates = resp_json.get("candidates") or []
                parts = (
                    ((candidates[0].get("content") or {}).get("parts") or [])
                    if candidates
                    else []
                )
                if not parts or "text" not in parts[0]:
                    raise ValueError(f"Empty Gemini response from {candidate}")
                text_content = str(parts[0]["text"]).strip()
                if text_content.startswith("```"):
                    text_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_content)
                return json.loads(text_content)
            except urllib.error.HTTPError as exc:
                err_msg = exc.read().decode("utf-8", errors="replace")
                last_error = f"HTTP {exc.code} ({candidate}): {err_msg}"
                if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(min(25.0, 3.0 * (2**attempt) + random.uniform(0.5, 1.5)))
                    continue
                break
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                ValueError,
            ) as exc:
                last_error = f"{type(exc).__name__} ({candidate}): {exc}"
                if attempt < 2 and isinstance(
                    exc, (urllib.error.URLError, TimeoutError, ConnectionError)
                ):
                    time.sleep(min(15.0, 3.0 * (2**attempt) + random.uniform(0.5, 1.5)))
                    continue
                break

    raise RuntimeError(
        f"Exhausted Gemini models ({', '.join(models_to_try)}). Last error: {last_error}"
    )


def _write_output(*, payload: dict[str, Any], output_path: str) -> None:
    rendered = json.dumps(payload, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
        print(f"Wrote review context ({len(rendered)} chars) to {output_path}")
        return
    print(rendered)


def run_prepare_local(*, args: argparse.Namespace) -> None:
    """Execute `prepare-local` to output line-annotated Git diffs and workspace rules."""
    diff_text = fetch_local_git_diff(
        staged=args.staged,
        commit=args.commit or "",
        diff_range=args.diff_range or "",
    )
    files_data = parse_and_annotate_diff(diff_text=diff_text)
    styleguides = load_styleguides(
        directories=(args.styleguides_dir, ".agents/rules", "conductor/code_styleguides")
    )
    payload = {
        "files": {
            fpath: {
                "valid_lines": sorted(item.valid_lines),
                "annotated_diff": item.annotated_diff,
            }
            for fpath, item in files_data.items()
        },
        "workspace_rules": styleguides,
    }
    _write_output(payload=payload, output_path=args.output or "")


def run_prepare_github(*, args: argparse.Namespace) -> None:
    """Execute `prepare-github` to bundle PR metadata, open threads, diff, and rules."""
    token = resolve_github_token()
    repo = resolve_github_repo(explicit_repo=args.repo or "")
    pr_info = get_pr_info(repo=repo, pr_number=str(args.pr), github_token=token)
    head_sha = ((pr_info.get("head") or {}).get("sha") or "").strip()
    base_sha = ((pr_info.get("base") or {}).get("sha") or "").strip()
    diff_text = fetch_pr_diff(
        repo=repo,
        pr_number=str(args.pr),
        github_token=token,
        base_sha=base_sha,
        head_sha=head_sha,
    )
    files_data = parse_and_annotate_diff(diff_text=diff_text)
    threads = fetch_open_threads(
        repo=repo,
        pr_number=str(args.pr),
        github_token=token,
        head_sha=head_sha,
        bot_only=args.bot_threads_only,
    )
    styleguides = load_styleguides(
        directories=(args.styleguides_dir, ".agents/rules", "conductor/code_styleguides")
    )
    payload = {
        "repo": repo,
        "pr_number": int(args.pr),
        "title": pr_info.get("title", ""),
        "head_sha": head_sha,
        "base_sha": base_sha,
        "open_threads": [
            build_thread_context(thread=t, head_sha=head_sha, files_data=files_data)
            for t in threads
        ],
        "files": {
            fpath: {
                "valid_lines": sorted(item.valid_lines),
                "annotated_diff": item.annotated_diff,
            }
            for fpath, item in files_data.items()
        },
        "workspace_rules": styleguides,
    }
    _write_output(payload=payload, output_path=args.output or "")


def run_publish_github(*, args: argparse.Namespace) -> None:
    """Execute `publish-github` to apply thread resolutions and post inline PR comments."""
    token = resolve_github_token()
    repo = resolve_github_repo(explicit_repo=args.repo or "")
    with open(args.input, encoding="utf-8") as handle:
        submission = json.load(handle)

    pr_info = get_pr_info(repo=repo, pr_number=str(args.pr), github_token=token)
    head_sha = (
        str(submission.get("head_sha") or "").strip()
        or ((pr_info.get("head") or {}).get("sha") or "").strip()
    )
    base_sha = ((pr_info.get("base") or {}).get("sha") or "").strip()
    diff_text = fetch_pr_diff(
        repo=repo,
        pr_number=str(args.pr),
        github_token=token,
        base_sha=base_sha,
        head_sha=head_sha,
    )
    files_data = parse_and_annotate_diff(diff_text=diff_text)

    for ev in submission.get("evaluations") or []:
        tid = str(ev.get("thread_id") or "").strip()
        reply = str(ev.get("reply") or "").strip()
        if not tid or not reply:
            continue
        reply_to_review_thread(github_token=token, thread_id=tid, body=reply)
        if ev.get("resolved"):
            resolve_review_thread(github_token=token, thread_id=tid)

    raw_comments = submission.get("comments") or []
    base_summary = str(submission.get("summary") or "Review complete.").strip()
    summary, aligned_comments = align_inline_comments(
        raw_comments=raw_comments,
        files_data=files_data,
        base_summary=base_summary,
    )
    post_github_review(
        repo=repo,
        pr_number=str(args.pr),
        github_token=token,
        head_sha=head_sha,
        summary=summary,
        inline_comments=aligned_comments,
    )
    print(
        f"Published PR #{args.pr} review ({len(aligned_comments)} inline comment(s))."
    )


def _run_ci_thread_pass(
    *,
    repo: str,
    pr_number: str,
    github_token: str,
    gemini_key: str,
    model: str,
    instructions: str,
    head_sha: str,
    files_data: dict[str, AnnotatedFileDiff],
) -> None:
    threads = fetch_open_threads(
        repo=repo,
        pr_number=pr_number,
        github_token=github_token,
        head_sha=head_sha,
        bot_only=True,
    )
    if not threads:
        return
    contexts = [
        build_thread_context(thread=t, head_sha=head_sha, files_data=files_data)
        for t in threads
    ]
    serialized = json.dumps(contexts, indent=2)[:MAX_PAYLOAD_CHARS]
    schema = {
        "type": "OBJECT",
        "properties": {
            "evaluations": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "thread_id": {"type": "STRING"},
                        "resolved": {"type": "BOOLEAN"},
                        "reply": {"type": "STRING"},
                    },
                    "required": ["thread_id", "resolved", "reply"],
                },
            }
        },
        "required": ["evaluations"],
    }
    prompt = (
        "Evaluate each prior open Pull Request review thread below against the latest "
        "diff and HEAD excerpt. Set `resolved` to true if addressed and write a concise "
        f"`reply` for every thread_id.\n\n{serialized}"
    )
    response = invoke_gemini_json(
        api_key=gemini_key,
        model=model,
        system_instructions=instructions,
        user_prompt=prompt,
        response_schema=schema,
    )
    for item in response.get("evaluations") or []:
        tid = str(item.get("thread_id") or "").strip()
        reply = str(item.get("reply") or "").strip()
        if not tid or not reply:
            continue
        reply_to_review_thread(github_token=github_token, thread_id=tid, body=reply)
        if item.get("resolved"):
            resolve_review_thread(github_token=github_token, thread_id=tid)


def run_ci() -> None:
    """Execute headless two-pass Gemini Pull Request review inside GitHub Actions."""
    repo = get_env_var(name="REPO")
    pr_number = get_env_var(name="PR_NUMBER")
    if not repo or not pr_number:
        raise ReviewConfigError("REPO and PR_NUMBER must be set in CI mode.")

    pr_author = get_env_var(name="PR_AUTHOR")
    is_merged_env = get_env_var(name="IS_MERGED")
    skip, reason = should_skip_review(
        pr_number=pr_number,
        pr_author=pr_author,
        is_merged=is_merged_env,
    )
    if skip:
        print(f"{reason} Skipping review.")
        return

    github_token = resolve_github_token()
    gemini_key = get_env_var(name="GEMINI_API_KEY")
    if not gemini_key:
        raise ReviewConfigError("GEMINI_API_KEY must be set in CI mode.")

    head_sha = get_env_var(name="HEAD_SHA")
    base_sha = get_env_var(name="BASE_SHA")
    if not head_sha or not base_sha or not pr_author or not is_merged_env:
        pr_info = get_pr_info(repo=repo, pr_number=pr_number, github_token=github_token)
        head_sha = head_sha or ((pr_info.get("head") or {}).get("sha") or "").strip()
        base_sha = base_sha or ((pr_info.get("base") or {}).get("sha") or "").strip()
        skip, reason = should_skip_review(
            pr_number=pr_number,
            pr_author=pr_author,
            is_merged=is_merged_env,
            pr_info=pr_info,
        )
        if skip:
            print(f"{reason} Skipping review.")
            return

    instructions_file = get_env_var(
        name="INSTRUCTIONS_FILE",
        default=".github/review-instructions.md",
    )
    styleguides_dir = get_env_var(name="STYLEGUIDES_DIR", default=".agents/rules")
    instructions = ""
    if os.path.isfile(instructions_file):
        with open(instructions_file, encoding="utf-8") as handle:
            instructions = handle.read()
    else:
        default_ref = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "references",
            "review-instructions.md",
        )
        if os.path.isfile(default_ref):
            with open(default_ref, encoding="utf-8") as handle:
                instructions = handle.read()

    styleguides = load_styleguides(
        directories=(styleguides_dir, ".agents/rules", "conductor/code_styleguides")
    )
    if styleguides:
        instructions = f"{instructions}\n\n{styleguides}".strip()

    user_comment = get_env_var(name="USER_COMMENT")
    if user_comment:
        focus = re.sub(r"^/review\b", "", user_comment, flags=re.IGNORECASE).strip()
        if focus:
            instructions += f'\n\n## Developer Focus\nPrioritise checking: "{focus}".'

    diff_text = fetch_pr_diff(
        repo=repo,
        pr_number=pr_number,
        github_token=github_token,
        base_sha=base_sha,
        head_sha=head_sha,
    )
    files_data = parse_and_annotate_diff(diff_text=diff_text)
    model = get_env_var(name="GEMINI_MODEL", default="gemini-3.8-flash")

    try:
        _run_ci_thread_pass(
            repo=repo,
            pr_number=pr_number,
            github_token=github_token,
            gemini_key=gemini_key,
            model=model,
            instructions=instructions,
            head_sha=head_sha,
            files_data=files_data,
        )
    except Exception as exc:
        print(f"Warning: Prior-thread validation pass failed: {exc}", file=sys.stderr)

    if not files_data:
        print("No reviewable code changes in diff.")
        return

    diff_payload = "\n\n".join(
        f"### File: {fpath}\n```diff\n{item.annotated_diff}\n```"
        for fpath, item in files_data.items()
    )[:MAX_PAYLOAD_CHARS]

    schema = {
        "type": "OBJECT",
        "properties": {
            "summary": {"type": "STRING"},
            "comments": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {"type": "STRING"},
                        "line": {"type": "INTEGER"},
                        "body": {"type": "STRING"},
                    },
                    "required": ["path", "line", "body"],
                },
            },
        },
        "required": ["summary", "comments"],
    }
    prompt = (
        "Review the Pull Request diff below. Anchor every comment to an exact new-file "
        f"line number shown before the colon (`  42: + code`).\n\n{diff_payload}"
    )
    review_output = invoke_gemini_json(
        api_key=gemini_key,
        model=model,
        system_instructions=instructions,
        user_prompt=prompt,
        response_schema=schema,
    )
    summary, aligned_comments = align_inline_comments(
        raw_comments=review_output.get("comments") or [],
        files_data=files_data,
        base_summary=str(review_output.get("summary") or "Review complete.").strip(),
    )
    post_github_review(
        repo=repo,
        pr_number=pr_number,
        github_token=github_token,
        head_sha=head_sha,
        summary=summary,
        inline_comments=aligned_comments,
        heading="### Gemini Code Review",
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for local, GitHub, and CI review modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    local = subparsers.add_parser("prepare-local", help="Annotate a local Git diff.")
    local.add_argument("--staged", action="store_true", help="Diff staged index only.")
    local.add_argument("--commit", default="", help="Show diff for a single commit SHA.")
    local.add_argument("--range", dest="diff_range", default="", help="Git diff range.")
    local.add_argument("--styleguides-dir", default="", help="Extra rules directory.")
    local.add_argument("--output", default="", help="Optional JSON output file path.")

    prep_gh = subparsers.add_parser(
        "prepare-github", help="Fetch PR metadata, open threads, and annotated diff."
    )
    prep_gh.add_argument("--pr", required=True, type=int, help="Pull Request number.")
    prep_gh.add_argument("--repo", default="", help="GitHub `<owner>/<name>`.")
    prep_gh.add_argument(
        "--bot-threads-only",
        action="store_true",
        help="Include only github-actions bot threads.",
    )
    prep_gh.add_argument("--styleguides-dir", default="", help="Extra rules directory.")
    prep_gh.add_argument("--output", default="", help="Optional JSON output file path.")

    pub_gh = subparsers.add_parser(
        "publish-github", help="Reply/resolve PR threads and post inline review."
    )
    pub_gh.add_argument("--pr", required=True, type=int, help="Pull Request number.")
    pub_gh.add_argument("--repo", default="", help="GitHub `<owner>/<name>`.")
    pub_gh.add_argument("--input", required=True, help="Path to approved review JSON.")

    subparsers.add_parser("ci", help="Run headless two-pass Gemini PR review in CI.")
    return parser


def main() -> None:
    """Dispatch CLI subcommands."""
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "prepare-local":
        run_prepare_local(args=args)
    elif args.command == "prepare-github":
        run_prepare_github(args=args)
    elif args.command == "publish-github":
        run_publish_github(args=args)
    elif args.command == "ci":
        run_ci()


if __name__ == "__main__":
    main()
