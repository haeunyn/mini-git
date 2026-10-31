"""명령어 실행기 — 토큰을 받아 Repository 를 호출하고 출력 문자열을 만든다."""

from .diff import diff_files, format_diff
from .errors import InvalidArgsError, MiniGitError
from .parser import parse_option, tokenize
from .repository import Repository

NO_PATH = "No path"


class CommandExecutor:
    def __init__(self, repo: Repository = None) -> None:
        self.repo = repo if repo is not None else Repository()

    def execute_line(self, line: str) -> str:
        tokens = tokenize(line)
        if not tokens:
            return ""
        try:
            return self.execute(tokens)
        except MiniGitError as exc:
            return exc.message
        except FileNotFoundError as exc:
            return f"File not found: {exc.filename}"

    def execute(self, tokens) -> str:
        # 명세: 명령어는 대소문자를 구분하지 않는다
        cmd = tokens[0].upper()
        args = tokens[1:]

        if cmd == "INIT":
            return self._init(args)
        if cmd == "BRANCH":
            return self._branch(args)
        if cmd == "SWITCH":
            return self._switch(args)
        if cmd == "COMMIT":
            return self._commit(args)
        if cmd == "LOG":
            return self._log(args)
        if cmd == "PATH":
            return self._path(args)
        if cmd == "ANCESTORS":
            return self._ancestors(args)
        if cmd == "SEARCH":
            return self._search(args)
        if cmd == "MERGE":
            return self._merge(args)
        if cmd == "DIFF":
            return self._diff(args)
        if cmd == "STATUS":
            return self._status(args)
        raise InvalidArgsError()

    # ---- 저장소 / 브랜치 ----
    def _init(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        self.repo.init(args[0])
        return (
            "Initialized repository.\n"
            f"Current branch: {self.repo.head_branch}\n"
            f"Current user: {self.repo.author}"
        )

    def _branch(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        self.repo.branch(args[0])
        return f"Created branch: {args[0]}"

    def _switch(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        self.repo.switch(args[0])
        return f"Switched to branch: {args[0]}"

    def _commit(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        commit = self.repo.commit(args[0])
        return f"[{commit.branch} {commit.hash}] {commit.message}"

    def _merge(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        commit = self.repo.merge(args[0])
        parents = " ".join(commit.parents)
        return (
            f"[{commit.branch} {commit.hash}] {commit.message}\n"
            f"Merge commit with parents: {parents}"
        )

    def _status(self, args) -> str:
        if args:
            raise InvalidArgsError()
        head = self.repo.head_commit()
        return (
            f"Current branch: {self.repo.head_branch}\n"
            f"Current user: {self.repo.author}\n"
            f"HEAD: {head if head else '(no commits yet)'}\n"
            f"Branches: {', '.join(self.repo.branch_names())}\n"
            f"Commits: {len(self.repo.commits)}"
        )

    # ---- 로그 ----
    def _log(self, args) -> str:
        if not args:
            commits = self.repo.log()
            return self._format_log(commits, show_branch=True)
        if len(args) == 1:
            field = parse_option(args[0], "sort-by")
            if field in ("date", "author"):
                return self._format_log(self.repo.log_sorted(field), show_branch=False)
        raise InvalidArgsError()

    def _format_log(self, commits, show_branch: bool) -> str:
        if not commits:
            return "No commits yet."
        lines = []
        for c in commits:
            marker = ""
            if show_branch:
                names = self.repo.branches_pointing_to(c.hash)
                if names:
                    marker = " [" + ", ".join(names) + "]"
            lines.append(f"commit {c.hash} ({c.author}, {c.timestamp}){marker}")
            lines.append(f"    {c.message}")
        return "\n".join(lines)

    # ---- 그래프 탐색 ----
    def _path(self, args) -> str:
        if len(args) != 2:
            raise InvalidArgsError()
        found = self.repo.path_between(args[0], args[1])
        if not found:
            return NO_PATH
        return "Path: " + " -> ".join(found)

    def _ancestors(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        found = self.repo.ancestors_of(args[0])
        if not found:
            return "No ancestors."
        lines = [f"Found {len(found)} ancestor(s):"]
        lines.extend(f"- {c.short()}" for c in found)
        return "\n".join(lines)

    # ---- 검색 ----
    def _search(self, args) -> str:
        if len(args) != 1:
            raise InvalidArgsError()
        author = parse_option(args[0], "author")
        if author is not None:
            found = self.repo.search_author(author)
            label = f"author '{author}'"
        else:
            found = self.repo.search_keyword(args[0])
            label = f"keyword '{args[0]}'"
        if not found:
            return f"No commit found for {label}."
        lines = [f"Found {len(found)} commit(s):"]
        lines.extend(f"- {c.short()}" for c in found)
        return "\n".join(lines)

    # ---- 보너스: diff ----
    def _diff(self, args) -> str:
        if len(args) != 2:
            raise InvalidArgsError()
        return format_diff(diff_files(args[0], args[1]))
