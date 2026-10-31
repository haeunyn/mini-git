"""REPL — mini-git> 프롬프트."""

import sys

from .commands import CommandExecutor
from .repository import Repository


class _FixedClock:
    """데모용 고정 시계 — 호출할 때마다 1초씩 흐른다.

    실제 시각을 쓰면 실행할 때마다 커밋 해시가 달라져서, 데모 스크립트에
    PATH <hash> <hash> 같은 명령을 미리 적어둘 수 없다. 시계를 고정하면
    해시가 항상 같게 나와 대본을 쓸 수 있다.
    """

    def __init__(self) -> None:
        self.seconds = 0

    def __call__(self) -> str:
        self.seconds += 1
        return f"2026-01-01 00:00:{self.seconds:02d}"

PROMPT = "mini-git> "
BANNER = (
    "Mini Git — 커밋 그래프(DAG) · 위상 정렬 · BFS · 역색인 · 직접 구현한 정렬\n"
    "명령어: INIT BRANCH SWITCH COMMIT LOG PATH ANCESTORS SEARCH MERGE DIFF STATUS\n"
    "종료: exit 또는 quit\n"
)


def run(stdin=None, show_banner: bool = True, deterministic: bool = False) -> int:
    stream = stdin if stdin is not None else sys.stdin
    repo = Repository(clock=_FixedClock()) if deterministic else Repository()
    executor = CommandExecutor(repo)
    interactive = stream is sys.stdin and sys.stdin.isatty()

    if show_banner and interactive:
        print(BANNER)

    while True:
        if interactive:
            try:
                line = input(PROMPT)
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
        else:
            line = stream.readline()
            if not line:
                return 0
            line = line.rstrip("\n")
            print(f"{PROMPT}{line}")

        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if interactive:
                print(stripped)
            continue
        if stripped.lower() in ("exit", "quit"):
            return 0

        output = executor.execute_line(stripped)
        if output:
            print(output)
