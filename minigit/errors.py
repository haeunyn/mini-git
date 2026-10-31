"""에러 메시지 표준 — 과제 명세가 정한 문구를 한곳에 모은다."""


class MiniGitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidArgsError(MiniGitError):
    def __init__(self) -> None:
        super().__init__("Invalid args")


class UnknownBranchError(MiniGitError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown branch: {name}")


class UnknownCommitError(MiniGitError):
    def __init__(self, commit_hash: str) -> None:
        super().__init__(f"Unknown commit: {commit_hash}")


class NotInitializedError(MiniGitError):
    def __init__(self) -> None:
        super().__init__("Repository not initialized. Run INIT <user_name> first.")
