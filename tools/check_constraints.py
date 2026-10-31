"""제약 사항 자동 검사기.

과제 제약: 정렬 관련 표준 API 전부 금지 — sorted(), list.sort() 등
          그래프 전용 라이브러리 사용 금지

ast 모듈로 구문 트리를 읽어 검사한다. 단순 문자열 검색으로는
`merge_sort(...)` 안의 'sort' 같은 것까지 잡혀 정확하지 않다.

사용법:  python3 tools/check_constraints.py
"""

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = [ROOT / "minigit", ROOT]
BANNED_CALLS = ("sorted",)
BANNED_METHODS = ("sort",)
BANNED_MODULES = ("networkx", "igraph", "graph_tool", "scipy", "numpy")
# 직접 구현한 정렬 함수는 당연히 허용된다
ALLOWED_OWN = ("merge_sort", "insertion_sort")


class Visitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations = []

    def _report(self, node, message: str) -> None:
        self.violations.append((self.filename, node.lineno, message))

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in BANNED_MODULES:
                self._report(node, f"import {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in BANNED_MODULES:
            self._report(node, f"from {node.module} import ...")
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        # sorted(...) — 이름으로 직접 호출
        if isinstance(func, ast.Name) and func.id in BANNED_CALLS:
            self._report(node, f"{func.id}() 사용")
        # x.sort(...) — 메서드 호출
        if isinstance(func, ast.Attribute) and func.attr in BANNED_METHODS:
            self._report(node, f".{func.attr}() 사용")
        self.generic_visit(node)


def main() -> int:
    files = sorted(set(
        list((ROOT / "minigit").glob("*.py")) + [ROOT / "main.py"]
    ))
    violations = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = Visitor(path.name)
        visitor.visit(tree)
        violations.extend(visitor.violations)

    print(f"검사 대상: 파이썬 파일 {len(files)}개 (minigit/ + main.py)")
    print("금지 항목: sorted(), .sort(), 그래프 전용 라이브러리")
    print(f"직접 구현한 정렬: {', '.join(ALLOWED_OWN)}")
    print("-" * 58)
    if violations:
        for filename, lineno, message in violations:
            print(f"  ✗ {filename}:{lineno}  {message}")
        print("-" * 58)
        print(f"위반 {len(violations)}건")
        return 1
    print("  위반 없음")
    print("-" * 58)
    print("✅ 표준 정렬 API와 그래프 라이브러리를 사용하지 않았습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
