"""보너스 1 — 두 텍스트 파일을 줄 단위로 비교한다.

LCS(최장 공통 부분수열) 로 "공통으로 남는 줄"을 먼저 찾고,
거기에 맞춰 추가(+)·삭제(-)·공통( ) 을 표시한다.

왜 단순 비교가 아니라 LCS 인가:
    두 파일을 1번 줄끼리, 2번 줄끼리 짝지어 비교하면, 중간에 한 줄만
    끼어들어도 그 뒤가 전부 "다른 줄"로 잡힌다. LCS 는 "순서를 지키면서
    가장 많이 겹치는 줄"을 찾으므로, 끼어든 줄 하나만 +로 표시된다.
    실제 git diff 도 같은 원리다.

시간복잡도 O(n × m). 표를 채우는 동적 계획법(DP)이다.
"""


def lcs_table(a, b):
    """a[:i] 와 b[:j] 의 최장 공통 부분수열 길이 표를 만든다."""
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            if a[i] == b[j]:
                table[i][j] = table[i + 1][j + 1] + 1   # 같은 줄이면 1 더하고 둘 다 전진
            else:
                table[i][j] = max(table[i + 1][j], table[i][j + 1])
    return table


def diff_lines(a, b):
    """(기호, 줄) 목록을 돌려준다. 기호는 ' ', '-', '+'."""
    table = lcs_table(a, b)
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            result.append((" ", a[i]))
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            result.append(("-", a[i]))   # a 에만 있다 = 삭제된 줄
            i += 1
        else:
            result.append(("+", b[j]))   # b 에만 있다 = 추가된 줄
            j += 1
    while i < len(a):
        result.append(("-", a[i])); i += 1
    while j < len(b):
        result.append(("+", b[j])); j += 1
    return result


def diff_files(path_a: str, path_b: str):
    """파일 두 개를 읽어 비교한다. 읽기 실패는 호출한 쪽에서 처리한다."""
    with open(path_a, encoding="utf-8") as f:
        a = f.read().splitlines()
    with open(path_b, encoding="utf-8") as f:
        b = f.read().splitlines()
    return diff_lines(a, b)


def format_diff(rows):
    """출력용 문자열로 만든다. 요약 줄을 마지막에 붙인다."""
    lines = [f"{symbol} {text}" for symbol, text in rows]
    added = sum(1 for s, _ in rows if s == "+")
    removed = sum(1 for s, _ in rows if s == "-")
    common = sum(1 for s, _ in rows if s == " ")
    lines.append(f"--- 공통 {common}줄, 추가 {added}줄, 삭제 {removed}줄")
    return "\n".join(lines)
