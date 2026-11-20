#!/usr/bin/env python3
"""Line-annotated Git diff and GitHub Pull Request review helper and CI runner."""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import http.client
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Sequence

CURRENT_GEMINI_MODELS: tuple[str, ...] = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)
DEFAULT_GEMINI_MODEL = CURRENT_GEMINI_MODELS[0]

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
DEFAULT_RULES_DIR = ".agents/rules"
ENCODING_UTF8 = "utf-8"
GIT_BINARY = "git"
GH_BINARY = "gh"
HTTP_POST = "POST"
USER_AGENT = "Marcel-Code-Review"
CONTENT_TYPE_JSON = "application/json"
GITHUB_ACCEPT_JSON = "application/vnd.github+json"
GITHUB_ACCEPT_DIFF = "application/vnd.github.v3.diff"
GITHUB_API_VERSION = "2022-11-28"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

FRONT_MATTER_PATTERN = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

MAX_PAYLOAD_CHARS = 120_000
DIFF_HEADER_MIN_PARTS = 4
EXCERPT_MAX_LINES = 250
EXCERPT_TARGET_THRESHOLD = 100
EXCERPT_HEAD_LINES = 40
EXCERPT_RADIUS = 45
MAX_LINE_SNAP_DISTANCE = 3
MAX_MODEL_ATTEMPTS = 3
HTTP_OK_MIN = 200
HTTP_OK_MAX = 299
HTTP_UNPROCESSABLE_ENTITY = 422
RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
SYSTEM_RANDOM = secrets.SystemRandom()


class ReviewConfigError(RuntimeError):
    """Raised when required CLI flags, binaries, tokens, or repo settings are missing."""

    @classmethod
    def missing_binary(cls, *, name: str) -> ReviewConfigError:
        """Build error when a required CLI executable is unavailable on PATH."""
        return cls(f"Executable not found on PATH: {name}")

    @classmethod
    def missing_github_token(cls) -> ReviewConfigError:
        """Build error when neither GITHUB_TOKEN nor `gh auth token` yields a token."""
        return cls("GITHUB_TOKEN is not set and `gh auth token` failed.")

    @classmethod
    def missing_repo(cls) -> ReviewConfigError:
        """Build error when `<owner>/<name>` cannot be resolved."""
        return cls("Pass --repo <owner/name> or set REPO.")

    @classmethod
    def missing_ci_env(cls, *, variable_names: str) -> ReviewConfigError:
        """Build error when required CI environment variables are unset."""
        return cls(
            f"Required CI environment variable(s) missing: {variable_names}"
        )


class ReviewApiError(RuntimeError):
    """Raised when an upstream GitHub or Gemini HTTPS call fails."""

    def __init__(self, message: str, *, status_code: int = 0) -> None:
        """Store failure details alongside optional HTTP status code."""
        super().__init__(message)
        self.status_code = status_code

    @classmethod
    def invalid_scheme(cls, *, url: str) -> ReviewApiError:
        """Build error when a non-HTTPS URL is supplied."""
        return cls(f"Only https:// URLs are permitted: {url}")

    @classmethod
    def http_status(
        cls, *, status_code: int, target: str, detail: str
    ) -> ReviewApiError:
        """Build error for a non-2xx HTTPS response."""
        return cls(
            f"HTTP {status_code} from {target}: {detail}",
            status_code=status_code,
        )

    @classmethod
    def graphql(cls, *, errors: Any) -> ReviewApiError:
        """Build error when GitHub GraphQL returns an `errors` list."""
        return cls(f"GitHub GraphQL error: {errors}")

    @classmethod
    def empty_gemini_response(cls, *, model: str) -> ReviewApiError:
        """Build error when Gemini returns no candidate text."""
        return cls(f"Empty Gemini response from {model}")

    @classmethod
    def exhausted_models(
        cls, *, models: Sequence[str], last_error: str
    ) -> ReviewApiError:
        """Build error when all candidate Gemini models and retries fail."""
        joined = ", ".join(models)
        return cls(
            f"Exhausted Gemini models ({joined}). Last error: {last_error}"
        )


@dataclasses.dataclass
class _DiffAccumulator:
    """Mutable collector for annotated diff lines and valid right-side line numbers."""

    valid_lines: set[int] = dataclasses.field(default_factory=set)
    lines: list[str] = dataclasses.field(default_factory=list)


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


@dataclasses.dataclass(frozen=True)
class GitHubPrTarget:
    """Coordinates and authentication context for a target GitHub Pull Request."""

    repo: str
    pr_number: str
    github_token: str
    head_sha: str = ""
    base_sha: str = ""


def _write_stdout(*, text: str) -> None:
    sys.stdout.write(f"{text}\n")


def _write_stderr(*, text: str) -> None:
    sys.stderr.write(f"{text}\n")


def get_env_var(*, name: str, default: str = "") -> str:
    """Return a stripped environment variable or its fallback default."""
    return os.environ.get(name, default).strip()


def _build_github_headers(
    *,
    github_token: str,
    accept: str = GITHUB_ACCEPT_JSON,
    content_type: str = "",
) -> dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {github_token}",
        "Accept": accept,
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _run_executable(
    *,
    binary: str,
    args: Sequence[str],
    suppress_stderr: bool = False,
) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        raise ReviewConfigError.missing_binary(name=binary)
    stderr_target = subprocess.DEVNULL if suppress_stderr else None
    completed = subprocess.run(  # noqa: S603
        [resolved, *args],
        check=True,
        capture_output=not suppress_stderr,
        stdout=subprocess.PIPE if suppress_stderr else None,
        stderr=stderr_target,
    )
    return completed.stdout.decode(ENCODING_UTF8, errors="replace")


def _send_https_request(
    *,
    url: str,
    headers: dict[str, str],
    method: str = "GET",
    body_bytes: bytes | None = None,
    timeout: int = 30,
) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise ReviewApiError.invalid_scheme(url=url)
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"
    conn = http.client.HTTPSConnection(parts.netloc, timeout=timeout)
    try:
        conn.request(method, path, body=body_bytes, headers=headers)
        response = conn.getresponse()
        payload = response.read().decode(ENCODING_UTF8, errors="replace")
    finally:
        conn.close()
    if not (HTTP_OK_MIN <= response.status <= HTTP_OK_MAX):
        raise ReviewApiError.http_status(
            status_code=response.status,
            target=parts.netloc,
            detail=payload,
        )
    return payload


def resolve_github_token() -> str:
    """Resolve a GitHub token from GITHUB_TOKEN, GH_TOKEN, or `gh auth token`."""
    token = get_env_var(name="GITHUB_TOKEN") or get_env_var(name="GH_TOKEN")
    if token:
        return token
    try:
        resolved = _run_executable(
            binary=GH_BINARY,
            args=("auth", "token"),
            suppress_stderr=True,
        ).strip()
    except (ReviewConfigError, subprocess.CalledProcessError, OSError) as exc:
        raise ReviewConfigError.missing_github_token() from exc
    if not resolved:
        raise ReviewConfigError.missing_github_token()
    return resolved


def resolve_github_repo(*, explicit_repo: str = "") -> str:
    """Resolve `<owner>/<name>` from explicit input, REPO env, or `gh repo view`."""
    repo = explicit_repo.strip() or get_env_var(name="REPO")
    if repo:
        return repo
    try:
        resolved = _run_executable(
            binary=GH_BINARY,
            args=(
                "repo",
                "view",
                "--json",
                "nameWithOwner",
                "-q",
                ".nameWithOwner",
            ),
            suppress_stderr=True,
        ).strip()
    except (ReviewConfigError, subprocess.CalledProcessError, OSError) as exc:
        raise ReviewConfigError.missing_repo() from exc
    if not resolved:
        raise ReviewConfigError.missing_repo()
    return resolved


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


def _extract_diff_target_path(*, header_line: str) -> str:
    parts = header_line.split()
    if len(parts) < DIFF_HEADER_MIN_PARTS:
        return ""
    b_path = parts[3]
    return b_path[2:] if b_path.startswith("b/") else b_path


def _append_diff_body_line(
    *,
    raw_line: str,
    new_line: int,
    bucket: _DiffAccumulator,
) -> int:
    if raw_line.startswith("+"):
        bucket.valid_lines.add(new_line)
        bucket.lines.append(f"{new_line:4d}: + {raw_line[1:]}")
        return new_line + 1
    if raw_line.startswith(" "):
        bucket.valid_lines.add(new_line)
        bucket.lines.append(f"{new_line:4d}:   {raw_line[1:]}")
        return new_line + 1
    if raw_line.startswith("-"):
        bucket.lines.append(f"    : - {raw_line[1:]}")
        return new_line
    bucket.lines.append(raw_line)
    return new_line


def parse_and_annotate_diff(*, diff_text: str) -> dict[str, AnnotatedFileDiff]:
    """Parse unified diff text into per-file hunks annotated with right-side line numbers."""
    raw_files: dict[str, _DiffAccumulator] = {}
    current_file = ""
    new_line: int | None = None

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            target_path = _extract_diff_target_path(header_line=raw_line)
            current_file = (
                ""
                if not target_path or _should_ignore_path(path=target_path)
                else target_path
            )
            if current_file:
                raw_files[current_file] = _DiffAccumulator()
            new_line = None
            continue

        if not current_file:
            continue

        hunk_match = HUNK_HEADER_PATTERN.match(raw_line)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            raw_files[current_file].lines.append(raw_line)
            continue

        if new_line is not None:
            new_line = _append_diff_body_line(
                raw_line=raw_line,
                new_line=new_line,
                bucket=raw_files[current_file],
            )

    return {
        fpath: AnnotatedFileDiff(
            path=fpath,
            valid_lines=frozenset(data.valid_lines),
            annotated_diff="\n".join(data.lines),
        )
        for fpath, data in raw_files.items()
        if data.valid_lines
    }


def load_styleguides(*, directories: Sequence[str]) -> str:
    """Load Markdown styleguides across candidate directories with YAML front matter stripped."""
    sections: list[str] = []
    seen_paths: set[Path] = set()
    for directory in directories:
        if not directory:
            continue
        dir_path = Path(directory)
        if not dir_path.is_dir():
            continue
        for md_path in sorted(dir_path.glob("*.md")):
            real = md_path.resolve()
            if real in seen_paths:
                continue
            seen_paths.add(real)
            raw_text = md_path.read_text(encoding=ENCODING_UTF8)
            content = FRONT_MATTER_PATTERN.sub("", raw_text).strip()
            if content:
                sections.append(f"## Rule: {md_path.name}\n\n{content}")
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
        args: tuple[str, ...] = ("show", "--format=", "-U3", commit)
    elif diff_range:
        args = ("diff", "-U3", diff_range)
    elif staged:
        args = ("diff", "--cached", "-U3")
    else:
        args = ("diff", "-U3", "HEAD")
    return _run_executable(binary=GIT_BINARY, args=args)


def get_pr_info(*, target: GitHubPrTarget) -> dict[str, Any]:
    """Fetch Pull Request metadata from the GitHub REST API."""
    url = f"{GITHUB_API_BASE}/repos/{target.repo}/pulls/{target.pr_number}"
    payload = _send_https_request(
        url=url,
        headers=_build_github_headers(github_token=target.github_token),
    )
    return json.loads(payload)


def fetch_pr_diff(*, target: GitHubPrTarget) -> str:
    """Fetch Pull Request unified diff from local Git history or the GitHub API."""
    if target.base_sha and target.head_sha:
        try:
            diff = _run_executable(
                binary=GIT_BINARY,
                args=("diff", "-U3", f"{target.base_sha}...{target.head_sha}"),
                suppress_stderr=True,
            )
            if diff.strip():
                return diff
        except (ReviewConfigError, subprocess.CalledProcessError, OSError):
            pass

    url = f"{GITHUB_API_BASE}/repos/{target.repo}/pulls/{target.pr_number}"
    return _send_https_request(
        url=url,
        headers=_build_github_headers(
            github_token=target.github_token,
            accept=GITHUB_ACCEPT_DIFF,
        ),
    )


def execute_github_graphql(
    *,
    github_token: str,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """Execute a GitHub GraphQL query or mutation and return its `data` mapping."""
    payload = json.dumps({"query": query, "variables": variables}).encode(
        ENCODING_UTF8
    )
    raw_resp = _send_https_request(
        url=GITHUB_GRAPHQL_URL,
        method=HTTP_POST,
        body_bytes=payload,
        headers=_build_github_headers(
            github_token=github_token,
            content_type=CONTENT_TYPE_JSON,
        ),
    )
    body = json.loads(raw_resp)
    errors = body.get("errors")
    if errors:
        raise ReviewApiError.graphql(errors=errors)
    return body.get("data") or {}


def _parse_iso_timestamp(*, value: str) -> datetime.datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"
    try:
        parsed = datetime.datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.UTC)
    return parsed


def _is_prior_thread_candidate(
    *,
    root_comment: dict[str, Any],
    head_sha: str,
    latest_dt: datetime.datetime | None,
    bot_only: bool,
) -> bool:
    author = (
        ((root_comment.get("author") or {}).get("login") or "").strip().lower()
    )
    if bot_only and author not in BOT_AUTHOR_LOGINS:
        return False
    commit_oid = (
        (root_comment.get("originalCommit") or {}).get("oid") or ""
    ).strip()
    created_dt = _parse_iso_timestamp(
        value=str(root_comment.get("createdAt") or "")
    )
    if head_sha and commit_oid and commit_oid == head_sha:
        return False
    if (
        latest_dt is not None
        and created_dt is not None
        and created_dt >= latest_dt
    ):
        return False
    return not (
        bot_only
        and not commit_oid
        and (latest_dt is None or created_dt is None)
    )


def _format_thread_replies(
    *, comment_nodes: Sequence[dict[str, Any]]
) -> tuple[str, ...]:
    replies: list[str] = []
    for node in comment_nodes:
        author = ((node.get("author") or {}).get("login") or "unknown").strip()
        body = str(node.get("body") or "").strip()
        if body:
            replies.append(f"{author}: {body}")
    return tuple(replies)


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
        if not _is_prior_thread_candidate(
            root_comment=root,
            head_sha=head_sha,
            latest_dt=latest_dt,
            bot_only=bot_only,
        ):
            continue

        thread_id = str(thread.get("id") or "").strip()
        path = str(thread.get("path") or "").strip()
        body = str(root.get("body") or "").strip()
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
                diff_hunk=str(root.get("diffHunk") or "").strip(),
                original_commit_oid=(
                    (root.get("originalCommit") or {}).get("oid") or ""
                ).strip(),
                created_at=str(root.get("createdAt") or "").strip(),
                replies=_format_thread_replies(comment_nodes=comments[1:]),
            )
        )
    return open_threads


def fetch_open_threads(
    *,
    target: GitHubPrTarget,
    bot_only: bool = True,
) -> list[OpenReviewThread]:
    """Fetch unresolved review threads on a Pull Request via GraphQL."""
    owner, name = target.repo.split("/", 1)
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
    data = execute_github_graphql(
        github_token=target.github_token,
        query=query,
        variables={
            "owner": owner,
            "name": name,
            "prNumber": int(target.pr_number),
        },
    )
    pr_data = (data.get("repository") or {}).get("pullRequest") or {}
    latest_oid = target.head_sha or str(pr_data.get("headRefOid") or "").strip()
    latest_date = ""
    commit_nodes = (pr_data.get("commits") or {}).get("nodes") or []
    if commit_nodes:
        commit_obj = commit_nodes[-1].get("commit") or {}
        latest_date = str(commit_obj.get("committedDate") or "").strip()
        if not latest_oid:
            latest_oid = str(commit_obj.get("oid") or "").strip()
    threads_data = (pr_data.get("reviewThreads") or {}).get("nodes") or []
    return filter_open_prior_threads(
        threads_data=threads_data,
        head_sha=latest_oid,
        latest_commit_date=latest_date,
        bot_only=bot_only,
    )


def _read_raw_file_at_head(*, path: str, head_sha: str) -> str | None:
    if head_sha:
        try:
            return _run_executable(
                binary=GIT_BINARY,
                args=("show", f"{head_sha}:{path}"),
                suppress_stderr=True,
            )
        except (ReviewConfigError, subprocess.CalledProcessError, OSError):
            pass
    file_path = Path(path)
    if file_path.is_file():
        try:
            return file_path.read_text(encoding=ENCODING_UTF8)
        except OSError:
            return None
    return None


def _read_file_at_head(
    *,
    path: str,
    head_sha: str,
    target_line: int | None = None,
) -> str | None:
    raw_content = _read_raw_file_at_head(path=path, head_sha=head_sha)
    if raw_content is None:
        return None

    numbered = [
        f"{idx:4d}: {line}"
        for idx, line in enumerate(raw_content.splitlines(), 1)
    ]
    if len(numbered) <= EXCERPT_MAX_LINES:
        return "\n".join(numbered)
    if target_line is not None and target_line > EXCERPT_TARGET_THRESHOLD:
        start_idx = max(EXCERPT_HEAD_LINES, target_line - EXCERPT_RADIUS)
        end_idx = min(len(numbered), target_line + EXCERPT_RADIUS)
        parts = ["\n".join(numbered[:EXCERPT_HEAD_LINES])]
        if start_idx > EXCERPT_HEAD_LINES:
            parts.append("... [lines omitted] ...")
        parts.append("\n".join(numbered[start_idx:end_idx]))
        if end_idx < len(numbered):
            parts.append("... [file truncated] ...")
        return "\n".join(parts)
    return (
        "\n".join(numbered[:EXCERPT_MAX_LINES]) + "\n... [file truncated] ..."
    )


def _fetch_commit_file_diff(
    *,
    original_commit_oid: str,
    head_sha: str,
    path: str,
) -> str:
    if not original_commit_oid or not head_sha:
        return ""
    try:
        return _run_executable(
            binary=GIT_BINARY,
            args=(
                "diff",
                "-U3",
                f"{original_commit_oid}..{head_sha}",
                "--",
                path,
            ),
            suppress_stderr=True,
        ).strip()
    except (ReviewConfigError, subprocess.CalledProcessError, OSError):
        return ""


def build_thread_context(
    *,
    thread: OpenReviewThread,
    head_sha: str,
    files_data: dict[str, AnnotatedFileDiff],
) -> dict[str, Any]:
    """Build structured validation context for a single open review thread."""
    focus_line = (
        thread.line if thread.line is not None else thread.original_line
    )
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
    execute_github_graphql(
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
    execute_github_graphql(
        github_token=github_token,
        query=mutation,
        variables={"threadId": thread_id},
    )


def _apply_thread_evaluations(
    *,
    github_token: str,
    evaluations: Sequence[dict[str, Any]],
) -> None:
    for evaluation in evaluations:
        tid = str(evaluation.get("thread_id") or "").strip()
        reply = str(evaluation.get("reply") or "").strip()
        if not tid or not reply:
            continue
        reply_to_review_thread(
            github_token=github_token,
            thread_id=tid,
            body=reply,
        )
        if evaluation.get("resolved"):
            resolve_review_thread(github_token=github_token, thread_id=tid)


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
        if (
            closest is not None
            and abs(closest - line) <= MAX_LINE_SNAP_DISTANCE
        ):
            valid_comments.append(
                {
                    "path": fpath,
                    "line": int(closest),
                    "side": "RIGHT",
                    "body": body,
                }
            )
        else:
            summary += f"\n\n- **Note on `{fpath}:{line}`**: {body}"

    return summary, valid_comments


def post_github_review(
    *,
    target: GitHubPrTarget,
    summary: str,
    inline_comments: Sequence[dict[str, Any]],
    heading: str = "### Code Review",
) -> None:
    """Submit a formal GitHub Pull Request Review with 422 summary fallback."""
    url = f"{GITHUB_API_BASE}/repos/{target.repo}/pulls/{target.pr_number}/reviews"
    headers = _build_github_headers(
        github_token=target.github_token,
        content_type=CONTENT_TYPE_JSON,
    )
    review_body = (
        summary if summary.startswith("### ") else f"{heading}\n\n{summary}"
    )
    payload = {
        "commit_id": target.head_sha,
        "body": review_body,
        "event": "COMMENT",
        "comments": list(inline_comments),
    }
    try:
        _send_https_request(
            url=url,
            method=HTTP_POST,
            headers=headers,
            body_bytes=json.dumps(payload).encode(ENCODING_UTF8),
        )
    except ReviewApiError as exc:
        if exc.status_code != HTTP_UNPROCESSABLE_ENTITY or not inline_comments:
            raise
        fallback_body = review_body + "\n\n### Inline Findings\n"
        for comment in inline_comments:
            fallback_body += (
                f"\n- **`{comment['path']}:{comment['line']}`**:\n"
                f"{comment['body']}\n"
            )
        fallback_payload = {
            "commit_id": target.head_sha,
            "body": fallback_body,
            "event": "COMMENT",
            "comments": [],
        }
        _send_https_request(
            url=url,
            method=HTTP_POST,
            headers=headers,
            body_bytes=json.dumps(fallback_payload).encode(ENCODING_UTF8),
        )


def _extract_gemini_json(*, raw_response: str, model: str) -> dict[str, Any]:
    resp_json = json.loads(raw_response)
    candidates = resp_json.get("candidates") or []
    parts = (
        ((candidates[0].get("content") or {}).get("parts") or [])
        if candidates
        else []
    )
    if not parts or "text" not in parts[0]:
        raise ReviewApiError.empty_gemini_response(model=model)
    text_content = str(parts[0]["text"]).strip()
    if text_content.startswith("```"):
        text_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_content)
    return json.loads(text_content)


def invoke_gemini_json(
    *,
    api_key: str,
    model: str,
    system_instructions: str,
    user_prompt: str,
    response_schema: dict[str, Any],
) -> dict[str, Any]:
    """Call the Gemini API with structured JSON output, retries, and model fallback."""
    models_to_try = [model, *(m for m in CURRENT_GEMINI_MODELS if m != model)]
    req_body = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instructions}]},
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": CONTENT_TYPE_JSON,
            "responseSchema": response_schema,
        },
    }
    data_bytes = json.dumps(req_body).encode(ENCODING_UTF8)
    last_error = "Unknown error"

    for candidate in models_to_try:
        url = f"{GEMINI_API_BASE}/{candidate}:generateContent?key={api_key}"
        for attempt in range(MAX_MODEL_ATTEMPTS):
            try:
                raw_resp = _send_https_request(
                    url=url,
                    method=HTTP_POST,
                    headers={"Content-Type": CONTENT_TYPE_JSON},
                    body_bytes=data_bytes,
                    timeout=60,
                )
                return _extract_gemini_json(
                    raw_response=raw_resp, model=candidate
                )
            except ReviewApiError as exc:
                last_error = str(exc)
                if (
                    exc.status_code in RETRYABLE_STATUS_CODES
                    and attempt < MAX_MODEL_ATTEMPTS - 1
                ):
                    delay = min(
                        25.0,
                        3.0 * (2**attempt) + SYSTEM_RANDOM.uniform(0.5, 1.5),
                    )
                    time.sleep(delay)
                    continue
                break
            except (OSError, TimeoutError, ValueError) as exc:
                last_error = f"{type(exc).__name__} ({candidate}): {exc}"
                if attempt < MAX_MODEL_ATTEMPTS - 1 and isinstance(
                    exc, (OSError, TimeoutError)
                ):
                    delay = min(
                        15.0,
                        3.0 * (2**attempt) + SYSTEM_RANDOM.uniform(0.5, 1.5),
                    )
                    time.sleep(delay)
                    continue
                break

    raise ReviewApiError.exhausted_models(
        models=models_to_try, last_error=last_error
    )


def _write_output(*, payload: dict[str, Any], output_path: str) -> None:
    rendered = json.dumps(payload, indent=2)
    if output_path:
        Path(output_path).write_text(f"{rendered}\n", encoding=ENCODING_UTF8)
        _write_stdout(
            text=(
                f"Wrote review context ({len(rendered)} chars) to {output_path}"
            )
        )
        return
    _write_stdout(text=rendered)


def run_prepare_local(*, args: argparse.Namespace) -> None:
    """Execute `prepare-local` to output line-annotated Git diffs and workspace rules."""
    diff_text = fetch_local_git_diff(
        staged=args.staged,
        commit=args.commit or "",
        diff_range=args.diff_range or "",
    )
    files_data = parse_and_annotate_diff(diff_text=diff_text)
    styleguides = load_styleguides(
        directories=(args.styleguides_dir, DEFAULT_RULES_DIR)
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
    initial_target = GitHubPrTarget(
        repo=resolve_github_repo(explicit_repo=args.repo or ""),
        pr_number=str(args.pr),
        github_token=resolve_github_token(),
    )
    pr_info = get_pr_info(target=initial_target)
    target = dataclasses.replace(
        initial_target,
        head_sha=str((pr_info.get("head") or {}).get("sha") or "").strip(),
        base_sha=str((pr_info.get("base") or {}).get("sha") or "").strip(),
    )
    files_data = parse_and_annotate_diff(diff_text=fetch_pr_diff(target=target))
    threads = fetch_open_threads(target=target, bot_only=args.bot_threads_only)
    styleguides = load_styleguides(
        directories=(args.styleguides_dir, DEFAULT_RULES_DIR)
    )
    payload = {
        "repo": target.repo,
        "pr_number": int(args.pr),
        "title": pr_info.get("title", ""),
        "head_sha": target.head_sha,
        "base_sha": target.base_sha,
        "open_threads": [
            build_thread_context(
                thread=t, head_sha=target.head_sha, files_data=files_data
            )
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
    submission = json.loads(Path(args.input).read_text(encoding=ENCODING_UTF8))
    initial_target = GitHubPrTarget(
        repo=resolve_github_repo(explicit_repo=args.repo or ""),
        pr_number=str(args.pr),
        github_token=resolve_github_token(),
    )
    pr_info = get_pr_info(target=initial_target)
    target = dataclasses.replace(
        initial_target,
        head_sha=(
            str(submission.get("head_sha") or "").strip()
            or str((pr_info.get("head") or {}).get("sha") or "").strip()
        ),
        base_sha=str((pr_info.get("base") or {}).get("sha") or "").strip(),
    )
    files_data = parse_and_annotate_diff(diff_text=fetch_pr_diff(target=target))
    _apply_thread_evaluations(
        github_token=target.github_token,
        evaluations=submission.get("evaluations") or [],
    )

    summary, aligned_comments = align_inline_comments(
        raw_comments=submission.get("comments") or [],
        files_data=files_data,
        base_summary=str(
            submission.get("summary") or "Review complete."
        ).strip(),
    )
    post_github_review(
        target=target,
        summary=summary,
        inline_comments=aligned_comments,
    )
    _write_stdout(
        text=(
            f"Published PR #{args.pr} review "
            f"({len(aligned_comments)} inline comment(s))."
        )
    )


def _run_ci_thread_pass(
    *,
    target: GitHubPrTarget,
    gemini_key: str,
    model: str,
    instructions: str,
    files_data: dict[str, AnnotatedFileDiff],
) -> None:
    threads = fetch_open_threads(target=target, bot_only=True)
    if not threads:
        return
    contexts = [
        build_thread_context(
            thread=t, head_sha=target.head_sha, files_data=files_data
        )
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
        "Evaluate each prior open Pull Request review thread below against "
        "the latest diff and HEAD excerpt. Set `resolved` to true if addressed "
        f"and write a concise `reply` for every thread_id.\n\n{serialized}"
    )
    response = invoke_gemini_json(
        api_key=gemini_key,
        model=model,
        system_instructions=instructions,
        user_prompt=prompt,
        response_schema=schema,
    )
    _apply_thread_evaluations(
        github_token=target.github_token,
        evaluations=response.get("evaluations") or [],
    )


def _load_ci_instructions() -> str:
    instructions_path = Path(
        get_env_var(
            name="INSTRUCTIONS_FILE", default=".github/review-instructions.md"
        )
    )
    default_ref = (
        Path(__file__).resolve().parent.parent
        / "references"
        / "review-instructions.md"
    )
    instructions = ""
    if instructions_path.is_file():
        instructions = instructions_path.read_text(encoding=ENCODING_UTF8)
    elif default_ref.is_file():
        instructions = default_ref.read_text(encoding=ENCODING_UTF8)

    styleguides_dir = get_env_var(
        name="STYLEGUIDES_DIR", default=DEFAULT_RULES_DIR
    )
    styleguides = load_styleguides(
        directories=(styleguides_dir, DEFAULT_RULES_DIR)
    )
    if styleguides:
        instructions = f"{instructions}\n\n{styleguides}".strip()

    user_comment = get_env_var(name="USER_COMMENT")
    if user_comment:
        focus = re.sub(
            r"^/review\b", "", user_comment, flags=re.IGNORECASE
        ).strip()
        if focus:
            instructions += (
                f'\n\n## Developer Focus\nPrioritise checking: "{focus}".'
            )
    return instructions


def _resolve_ci_pr_target() -> GitHubPrTarget | None:
    repo = get_env_var(name="REPO")
    pr_number = get_env_var(name="PR_NUMBER")
    if not repo or not pr_number:
        raise ReviewConfigError.missing_ci_env(variable_names="REPO, PR_NUMBER")

    pr_author = get_env_var(name="PR_AUTHOR")
    is_merged_env = get_env_var(name="IS_MERGED")
    skip, reason = should_skip_review(
        pr_number=pr_number,
        pr_author=pr_author,
        is_merged=is_merged_env,
    )
    if skip:
        _write_stdout(text=f"{reason} Skipping review.")
        return None

    target = GitHubPrTarget(
        repo=repo,
        pr_number=pr_number,
        github_token=resolve_github_token(),
        head_sha=get_env_var(name="HEAD_SHA"),
        base_sha=get_env_var(name="BASE_SHA"),
    )
    if target.head_sha and target.base_sha and pr_author and is_merged_env:
        return target

    pr_info = get_pr_info(target=target)
    skip, reason = should_skip_review(
        pr_number=pr_number,
        pr_author=pr_author,
        is_merged=is_merged_env,
        pr_info=pr_info,
    )
    if skip:
        _write_stdout(text=f"{reason} Skipping review.")
        return None

    return dataclasses.replace(
        target,
        head_sha=target.head_sha
        or str((pr_info.get("head") or {}).get("sha") or "").strip(),
        base_sha=target.base_sha
        or str((pr_info.get("base") or {}).get("sha") or "").strip(),
    )


def run_ci() -> None:
    """Execute headless two-pass Gemini Pull Request review inside GitHub Actions."""
    gemini_key = get_env_var(name="GEMINI_API_KEY")
    if not gemini_key:
        raise ReviewConfigError.missing_ci_env(variable_names="GEMINI_API_KEY")

    target = _resolve_ci_pr_target()
    if target is None:
        return

    instructions = _load_ci_instructions()
    files_data = parse_and_annotate_diff(diff_text=fetch_pr_diff(target=target))
    model = get_env_var(name="GEMINI_MODEL", default=DEFAULT_GEMINI_MODEL)

    try:
        _run_ci_thread_pass(
            target=target,
            gemini_key=gemini_key,
            model=model,
            instructions=instructions,
            files_data=files_data,
        )
    except (ReviewApiError, OSError, ValueError) as exc:
        _write_stderr(
            text=f"Warning: Prior-thread validation pass failed: {exc}"
        )

    if not files_data:
        _write_stdout(text="No reviewable code changes in diff.")
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
        "Review the Pull Request diff below. Anchor every comment to an exact "
        "new-file line number shown before the colon (`  42: + code`).\n\n"
        f"{diff_payload}"
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
        base_summary=str(
            review_output.get("summary") or "Review complete."
        ).strip(),
    )
    post_github_review(
        target=target,
        summary=summary,
        inline_comments=aligned_comments,
        heading="### Gemini Code Review",
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for local, GitHub, and CI review modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    local = subparsers.add_parser(
        "prepare-local", help="Annotate a local Git diff."
    )
    local.add_argument(
        "--staged", action="store_true", help="Diff staged index only."
    )
    local.add_argument(
        "--commit", default="", help="Show diff for a single commit SHA."
    )
    local.add_argument(
        "--range", dest="diff_range", default="", help="Git diff range."
    )
    local.add_argument(
        "--styleguides-dir", default="", help="Extra rules directory."
    )
    local.add_argument(
        "--output", default="", help="Optional JSON output file path."
    )

    prep_gh = subparsers.add_parser(
        "prepare-github",
        help="Fetch PR metadata, open threads, and annotated diff.",
    )
    prep_gh.add_argument(
        "--pr", required=True, type=int, help="Pull Request number."
    )
    prep_gh.add_argument("--repo", default="", help="GitHub `<owner>/<name>`.")
    prep_gh.add_argument(
        "--bot-threads-only",
        action="store_true",
        help="Include only github-actions bot threads.",
    )
    prep_gh.add_argument(
        "--styleguides-dir", default="", help="Extra rules directory."
    )
    prep_gh.add_argument(
        "--output", default="", help="Optional JSON output file path."
    )

    pub_gh = subparsers.add_parser(
        "publish-github",
        help="Reply/resolve PR threads and post inline review.",
    )
    pub_gh.add_argument(
        "--pr", required=True, type=int, help="Pull Request number."
    )
    pub_gh.add_argument("--repo", default="", help="GitHub `<owner>/<name>`.")
    pub_gh.add_argument(
        "--input", required=True, help="Path to approved review JSON."
    )

    subparsers.add_parser(
        "ci", help="Run headless two-pass Gemini PR review in CI."
    )
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
