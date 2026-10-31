"""커밋 노드 — Mini Git 그래프의 꼭짓점 하나.

실제 Git 의 커밋도 이것과 거의 같다. 파일 내용은 따로 저장하고,
커밋 객체 자체는 "누가, 언제, 무슨 메시지로, 어떤 커밋 다음에"만 들고 있다.
"""

import hashlib


class Commit:
    """커밋 하나.

    parents 가 리스트인 이유:
        보통은 부모가 1개지만, merge 커밋은 2개를 갖는다.
        최초 커밋은 0개다. 그래서 개수를 고정할 수 없다.
    """

    __slots__ = ("hash", "message", "author", "timestamp", "parents", "branch")

    def __init__(self, commit_hash, message, author, timestamp, parents, branch):
        self.hash = commit_hash
        self.message = message
        self.author = author
        self.timestamp = timestamp      # "YYYY-MM-DD HH:MM:SS" 문자열
        self.parents = parents          # 부모 커밋 해시 목록
        self.branch = branch            # 어느 브랜치에서 만들어졌는지(출력용)

    def is_merge(self) -> bool:
        return len(self.parents) >= 2

    def short(self) -> str:
        return f"{self.hash}: {self.message}"

    def __repr__(self) -> str:
        return f"Commit({self.hash}, {self.message!r}, parents={self.parents})"


def make_hash(counter: int, message: str, author: str, timestamp: str) -> str:
    """커밋 해시를 만든다 — 6자리 16진수.

    왜 내용으로 해시를 만드나:
        실제 Git 도 "내용을 해시한 값"을 커밋 ID 로 쓴다(내용 주소 지정).
        같은 내용이면 같은 ID 가 나오고, 한 글자만 바뀌어도 ID 가 완전히 달라진다.

    counter 를 섞는 이유:
        같은 사람이 같은 초에 같은 메시지로 커밋하면 해시가 겹칠 수 있다.
        세션 내에서 1씩 증가하는 counter 를 넣어 충돌 가능성을 없앤다.

    길이를 6자로 고정한 이유:
        PATH 명령이 "최단 경로가 여러 개면 사전순으로 가장 작은 것"을 고르는데,
        해시 길이가 들쭉날쭉하면 문자열 비교 결과가 직관과 어긋난다.
        길이가 같으면 앞에서부터 한 글자씩 비교하는 것이 곧 사전순이 된다.
    """
    seed = f"{counter}|{message}|{author}|{timestamp}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:6]
