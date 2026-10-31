"""Mini Git 테스트.

가짜 시계를 주입해 타임스탬프를 1초씩 증가시킨다.
덕분에 커밋 해시와 정렬 결과가 매번 똑같이 나와 검증이 가능하다.
"""

import unittest

from minigit.commands import CommandExecutor
from minigit.diff import diff_lines
from minigit.graph import ancestors, shortest_path, topological_order
from minigit.index import InvertedIndex
from minigit.repository import Repository
from minigit.sorting import insertion_sort, merge_sort


class FakeClock:
    """호출할 때마다 1초씩 흐르는 가짜 시계."""

    def __init__(self) -> None:
        self.seconds = 0

    def __call__(self) -> str:
        self.seconds += 1
        return f"2026-01-01 00:00:{self.seconds:02d}"


def build_repo():
    """테스트용 저장소.

        c1 ── c2(feature)
         └─── c3(main)

    c2 와 c3 는 형제다 — 서로 조상 관계가 아니다.
    """
    repo = Repository(clock=FakeClock())
    repo.init("Alice")
    c1 = repo.commit("Initial commit")
    repo.branch("feature")
    repo.switch("feature")
    c2 = repo.commit("Add login feature")
    repo.switch("main")
    c3 = repo.commit("Add payment feature")
    return repo, c1, c2, c3


class TestSorting(unittest.TestCase):
    def test_두_정렬이_같은_결과를_낸다(self):
        data = [5, 3, 9, 1, 7, 3, 0]
        expected = [0, 1, 3, 3, 5, 7, 9]
        self.assertEqual(merge_sort(data), expected)
        self.assertEqual(insertion_sort(data), expected)

    def test_안정_정렬이다(self):
        # 키가 같은 항목의 원래 순서가 유지되어야 한다
        data = [("b", 1), ("a", 1), ("b", 2), ("a", 2)]
        key = lambda x: x[0]
        expected = [("a", 1), ("a", 2), ("b", 1), ("b", 2)]
        self.assertEqual(merge_sort(data, key=key), expected)
        self.assertEqual(insertion_sort(data, key=key), expected)

    def test_원본을_바꾸지_않는다(self):
        data = [3, 1, 2]
        merge_sort(data)
        insertion_sort(data)
        self.assertEqual(data, [3, 1, 2])

    def test_빈_리스트와_한개(self):
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(merge_sort([1]), [1])
        self.assertEqual(insertion_sort([]), [])


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.repo, self.c1, self.c2, self.c3 = build_repo()

    def test_위상정렬은_부모를_자식보다_먼저_놓는다(self):
        order = topological_order(self.repo.commits)
        self.assertEqual(order[0], self.c1.hash)          # 최초 커밋이 맨 앞
        self.assertIn(self.c2.hash, order)
        self.assertIn(self.c3.hash, order)
        # 모든 커밋에 대해 부모가 먼저 나와야 한다
        position = {h: i for i, h in enumerate(order)}
        for h, commit in self.repo.commits.items():
            for parent in commit.parents:
                self.assertLess(position[parent], position[h])

    def test_조상_탐색(self):
        found = ancestors(self.repo.commits, self.c2.hash)
        self.assertEqual(found, {self.c1.hash})
        self.assertEqual(ancestors(self.repo.commits, self.c1.hash), set())

    def test_형제_커밋_사이에도_경로가_있다(self):
        # 무방향으로 보면 c2 -> c1 -> c3 로 갈 수 있다
        path = shortest_path(self.repo.commits, self.c2.hash, self.c3.hash)
        self.assertEqual(path, [self.c2.hash, self.c1.hash, self.c3.hash])

    def test_자기_자신까지의_경로(self):
        self.assertEqual(
            shortest_path(self.repo.commits, self.c1.hash, self.c1.hash),
            [self.c1.hash],
        )

    def test_연결되지_않은_커밋은_경로가_없다(self):
        # 새 저장소를 만들면 기존 커밋과 이어지지 않는다
        other = Repository(clock=FakeClock())
        other.init("Bob")
        lonely = other.commit("Unrelated")
        merged = dict(self.repo.commits)
        merged[lonely.hash] = lonely
        self.assertIsNone(shortest_path(merged, self.c1.hash, lonely.hash))

    def test_merge커밋은_부모가_둘이다(self):
        self.repo.switch("main")
        merge_commit = self.repo.merge("feature")
        self.assertTrue(merge_commit.is_merge())
        self.assertEqual(len(merge_commit.parents), 2)
        # merge 이후엔 c2 도 조상이 된다
        found = ancestors(self.repo.commits, merge_commit.hash)
        self.assertIn(self.c2.hash, found)
        self.assertIn(self.c3.hash, found)


class TestInvertedIndex(unittest.TestCase):
    def test_토큰화는_소문자로_문장부호를_떼고(self):
        self.assertEqual(
            InvertedIndex.tokenize("Add LOGIN feature."), ["add", "login", "feature"]
        )

    def test_키워드와_작성자_양쪽_인덱스(self):
        repo, c1, c2, c3 = build_repo()
        self.assertEqual(repo.index.find_by_keyword("login"), [c2.hash])
        self.assertEqual(len(repo.index.find_by_author("Alice")), 3)
        self.assertEqual(repo.index.find_by_keyword("없는단어"), [])

    def test_검색은_대소문자를_가리지_않는다(self):
        repo, _, c2, _ = build_repo()
        self.assertEqual(repo.index.find_by_keyword("LOGIN"), [c2.hash])


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.repo, self.c1, self.c2, self.c3 = build_repo()
        self.ex = CommandExecutor(self.repo)

    def test_INIT_출력(self):
        ex = CommandExecutor(Repository(clock=FakeClock()))
        out = ex.execute_line('INIT "Alice"')
        self.assertIn("Initialized repository.", out)
        self.assertIn("Current branch: main", out)
        self.assertIn("Current user: Alice", out)

    def test_명령어는_대소문자를_가리지_않는다(self):
        self.assertIn("Created branch", self.ex.execute_line("branch hotfix"))
        self.assertIn("Created branch", self.ex.execute_line("BRANCH hotfix2"))

    def test_없는_브랜치로_전환하면_에러(self):
        self.assertEqual(
            self.ex.execute_line("SWITCH 없는브랜치"), "Unknown branch: 없는브랜치"
        )

    def test_없는_커밋을_조회하면_에러(self):
        self.assertEqual(
            self.ex.execute_line("ANCESTORS zzzzzz"), "Unknown commit: zzzzzz"
        )

    def test_인자_개수가_틀리면_Invalid_args(self):
        self.assertEqual(self.ex.execute_line("INIT"), "Invalid args")
        self.assertEqual(self.ex.execute_line("PATH onlyone"), "Invalid args")
        self.assertEqual(self.ex.execute_line("UNKNOWNCMD"), "Invalid args")

    def test_경로가_없으면_No_path(self):
        other = Repository(clock=FakeClock())
        other.init("Bob")
        lonely = other.commit("Unrelated")
        self.repo.commits[lonely.hash] = lonely
        self.assertEqual(
            self.ex.execute_line(f"PATH {self.c1.hash} {lonely.hash}"), "No path"
        )

    def test_PATH_출력_형식(self):
        out = self.ex.execute_line(f"PATH {self.c2.hash} {self.c3.hash}")
        self.assertEqual(
            out, f"Path: {self.c2.hash} -> {self.c1.hash} -> {self.c3.hash}"
        )

    def test_SEARCH_키워드와_작성자(self):
        out = self.ex.execute_line("SEARCH login")
        self.assertIn("Found 1 commit(s):", out)
        self.assertIn(self.c2.hash, out)
        out = self.ex.execute_line("SEARCH --author=Alice")
        self.assertIn("Found 3 commit(s):", out)
        self.assertIn("No commit found", self.ex.execute_line("SEARCH --author=Bob"))

    def test_LOG_정렬_옵션(self):
        self.assertIn("commit", self.ex.execute_line("LOG --sort-by=date"))
        self.assertIn("commit", self.ex.execute_line("LOG --sort-by=author"))
        self.assertEqual(self.ex.execute_line("LOG --sort-by=없는기준"), "Invalid args")

    def test_따옴표로_감싼_메시지의_공백이_유지된다(self):
        self.ex.execute_line('COMMIT "Fix a very long bug"')
        out = self.ex.execute_line("SEARCH very")
        self.assertIn("Fix a very long bug", out)

    def test_초기화_전에는_명령이_막힌다(self):
        ex = CommandExecutor(Repository(clock=FakeClock()))
        self.assertIn("not initialized", ex.execute_line('COMMIT "x"'))


class TestDiff(unittest.TestCase):
    def test_끼어든_줄만_추가로_표시된다(self):
        a = ["사과", "바나나", "포도"]
        b = ["사과", "딸기", "바나나", "포도"]
        rows = diff_lines(a, b)
        self.assertEqual(
            rows,
            [(" ", "사과"), ("+", "딸기"), (" ", "바나나"), (" ", "포도")],
        )

    def test_삭제와_추가가_함께(self):
        rows = diff_lines(["a", "b"], ["a", "c"])
        symbols = [s for s, _ in rows]
        self.assertIn("-", symbols)
        self.assertIn("+", symbols)

    def test_같은_파일은_전부_공통(self):
        rows = diff_lines(["a", "b"], ["a", "b"])
        self.assertTrue(all(s == " " for s, _ in rows))


if __name__ == "__main__":
    unittest.main()
