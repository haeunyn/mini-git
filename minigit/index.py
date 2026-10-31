"""역색인(Inverted Index) — 검색을 빠르게 만드는 자료구조.

'역(inverted)'인 이유:
    보통은 커밋 → 그 커밋의 단어들 (정방향)
    역색인은 뒤집어서 단어 → 그 단어가 들어 있는 커밋들

왜 빠른가 (시간복잡도):
    순회 검색: 커밋이 N개, 메시지 평균 길이 L 이면 매번 O(N × L)
    역색인   : 단어로 바로 찾으므로 O(1) + 결과 개수 K → O(K)
    커밋이 1만 개여도 "login"이 든 커밋이 3개면 3개만 꺼낸다.

대가: 커밋할 때 인덱스를 갱신하는 비용과 메모리를 더 쓴다.
     검색을 자주 하고 쓰기가 드물면 이득이다(검색 엔진이 전부 이 구조다).
"""


class InvertedIndex:
    """키워드 → 커밋 해시 목록, 작성자 → 커밋 해시 목록."""

    def __init__(self) -> None:
        self._by_keyword = {}  # 소문자 단어 -> [commit_hash, ...]
        self._by_author = {}   # 작성자 이름 -> [commit_hash, ...]

    @staticmethod
    def tokenize(message: str):
        """메시지를 검색용 토큰으로 쪼갠다.

        명세의 최소 기준: 공백으로 나누고(split) 소문자로 바꾼다(lower).
        추가로 양끝 문장부호를 떼어 낸다 — "login." 과 "login" 이 다른
        단어로 잡히면 검색이 잘 안 되기 때문이다.
        """
        tokens = []
        for raw in message.split():
            token = raw.strip(".,!?;:()[]{}\"'").lower()
            if token:
                tokens.append(token)
        return tokens

    def add(self, commit) -> None:
        """커밋 하나를 두 인덱스에 모두 등록한다."""
        for token in self.tokenize(commit.message):
            bucket = self._by_keyword.get(token)
            if bucket is None:
                bucket = []
                self._by_keyword[token] = bucket
            if commit.hash not in bucket:
                bucket.append(commit.hash)

        bucket = self._by_author.get(commit.author)
        if bucket is None:
            bucket = []
            self._by_author[commit.author] = bucket
        bucket.append(commit.hash)

    def find_by_keyword(self, keyword: str):
        """키워드로 커밋 해시 목록을 찾는다. 없으면 빈 리스트."""
        return list(self._by_keyword.get(keyword.lower().strip(), []))

    def find_by_author(self, author: str):
        return list(self._by_author.get(author, []))

    def keyword_count(self) -> int:
        return len(self._by_keyword)

    def author_count(self) -> int:
        return len(self._by_author)
