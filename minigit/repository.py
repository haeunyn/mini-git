"""저장소 — 커밋 그래프 + 브랜치 + HEAD 를 들고 있는 상태 덩어리.

실제 Git 의 .git 폴더에 해당한다. 다만 과제 범위대로 파일에 저장하지 않고
메모리에만 둔다(프로그램을 끄면 사라진다).

브랜치란 무엇인가 — 이 미션의 핵심 개념:
    브랜치는 '커밋 묶음'이 아니라 **커밋 하나를 가리키는 이름표**다.
    self._branches 가 {브랜치이름: 커밋해시} 인 이유가 그것이다.
    새 커밋을 만들면 그 이름표만 새 커밋으로 옮겨 간다.
    그래서 브랜치를 만드는 비용이 거의 0이다(이름표 하나 더 붙이는 것).
    HEAD 는 '지금 어느 이름표 위에 서 있는가'를 가리킨다.
"""

import time

from .commit import Commit, make_hash
from .errors import NotInitializedError, UnknownBranchError, UnknownCommitError
from .graph import ancestors, shortest_path, topological_order
from .index import InvertedIndex
from .sorting import merge_sort

MAIN_BRANCH = "main"


class Repository:
    def __init__(self, clock=None) -> None:
        # clock 주입: 테스트에서 타임스탬프를 마음대로 정하기 위해서다.
        self._clock = clock or (lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
        self.initialized = False
        self.author = None
        self._commits = {}      # hash -> Commit
        self._branches = {}     # 브랜치 이름 -> 커밋 해시 (이름표)
        self.head_branch = None # 지금 서 있는 브랜치 이름
        self._index = InvertedIndex()
        self._counter = 0       # 해시 유일성 보장용

    # ---- 상태 확인 ----
    def _require_init(self) -> None:
        if not self.initialized:
            raise NotInitializedError()

    @property
    def commits(self):
        return self._commits

    @property
    def index(self):
        return self._index

    def branch_names(self):
        return merge_sort(list(self._branches.keys()), key=lambda n: n)

    def head_commit(self):
        """HEAD 가 가리키는 커밋 해시. 아직 커밋이 없으면 None."""
        if self.head_branch is None:
            return None
        return self._branches.get(self.head_branch)

    def get_commit(self, commit_hash: str) -> Commit:
        commit = self._commits.get(commit_hash)
        if commit is None:
            raise UnknownCommitError(commit_hash)
        return commit

    # ---- 명령 구현 ----
    def init(self, user_name: str) -> None:
        """저장소 초기화. main 브랜치를 만들고 HEAD 를 올린다."""
        self.__init__(clock=self._clock)   # 같은 세션에서 다시 INIT 하면 초기화
        self.initialized = True
        self.author = user_name
        self._branches[MAIN_BRANCH] = None  # 아직 커밋이 없으니 가리킬 곳이 없다
        self.head_branch = MAIN_BRANCH

    def branch(self, name: str) -> None:
        """현재 HEAD 를 가리키는 새 이름표를 만든다."""
        self._require_init()
        self._branches[name] = self.head_commit()

    def switch(self, name: str) -> None:
        """HEAD 를 다른 이름표 위로 옮긴다."""
        self._require_init()
        if name not in self._branches:
            raise UnknownBranchError(name)
        self.head_branch = name

    def commit(self, message: str, extra_parent: str = None) -> Commit:
        """현재 HEAD 를 부모로 하는 새 커밋을 만든다.

        extra_parent 가 있으면 부모가 2개인 merge 커밋이 된다(보너스 2).
        """
        self._require_init()
        parents = []
        head = self.head_commit()
        if head is not None:
            parents.append(head)
        if extra_parent is not None and extra_parent != head:
            parents.append(extra_parent)

        timestamp = self._clock()
        self._counter += 1
        commit_hash = make_hash(self._counter, message, self.author, timestamp)
        # 만에 하나 겹치면 counter 를 올려 다시 만든다(유일성 보장)
        while commit_hash in self._commits:
            self._counter += 1
            commit_hash = make_hash(self._counter, message, self.author, timestamp)

        new_commit = Commit(
            commit_hash, message, self.author, timestamp, parents, self.head_branch
        )
        self._commits[commit_hash] = new_commit
        self._branches[self.head_branch] = commit_hash  # 이름표를 옮긴다
        self._index.add(new_commit)                     # 역색인 갱신
        return new_commit

    def merge(self, branch_name: str) -> Commit:
        """보너스 2 — 대상 브랜치의 HEAD 를 두 번째 부모로 하는 merge 커밋."""
        self._require_init()
        if branch_name not in self._branches:
            raise UnknownBranchError(branch_name)
        target = self._branches[branch_name]
        message = f"Merge branch '{branch_name}' into {self.head_branch}"
        return self.commit(message, extra_parent=target)

    # ---- 조회 ----
    def log(self):
        """부모가 자식보다 먼저 오도록 정렬된 커밋 목록."""
        self._require_init()
        return [self._commits[h] for h in topological_order(self._commits)]

    def log_sorted(self, field: str):
        """date 또는 author 기준 정렬. 직접 구현한 병합 정렬을 쓴다."""
        self._require_init()
        commits = list(self._commits.values())
        if field == "date":
            # 동률이면 해시로 — 결과가 매번 같아야 테스트가 가능하다
            return merge_sort(commits, key=lambda c: (c.timestamp, c.hash))
        if field == "author":
            return merge_sort(commits, key=lambda c: (c.author, c.timestamp, c.hash))
        return None

    def ancestors_of(self, commit_hash: str):
        self._require_init()
        self.get_commit(commit_hash)
        found = ancestors(self._commits, commit_hash)
        return merge_sort(
            [self._commits[h] for h in found],
            key=lambda c: (c.timestamp, c.hash),
        )

    def path_between(self, a: str, b: str):
        self._require_init()
        self.get_commit(a)
        self.get_commit(b)
        return shortest_path(self._commits, a, b)

    def search_keyword(self, keyword: str):
        self._require_init()
        hashes = self._index.find_by_keyword(keyword)
        return self._to_commits(hashes)

    def search_author(self, author: str):
        self._require_init()
        hashes = self._index.find_by_author(author)
        return self._to_commits(hashes)

    def _to_commits(self, hashes):
        commits = [self._commits[h] for h in hashes if h in self._commits]
        return merge_sort(commits, key=lambda c: (c.timestamp, c.hash))

    def branches_pointing_to(self, commit_hash: str):
        """이 커밋을 가리키는 브랜치 이름들(로그 출력용)."""
        names = [n for n, h in self._branches.items() if h == commit_hash]
        return merge_sort(names, key=lambda n: n)
