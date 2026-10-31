"""정렬 알고리즘 직접 구현 — sorted() / list.sort() 사용 금지.

두 가지를 구현한다:
    merge_sort      평균·최악 O(n log n), 안정 정렬, 추가 메모리 O(n)
    insertion_sort  평균·최악 O(n²), 안정 정렬, 추가 메모리 O(1)

"안정 정렬(stable)"이란:
    정렬 기준이 같은 두 항목의 원래 순서가 뒤바뀌지 않는 것.
    예를 들어 작성자 기준으로 정렬할 때, 같은 작성자의 커밋들은
    원래 순서(= 커밋한 순서)를 그대로 유지한다. 이게 유지되지 않으면
    "같은 사람 커밋이 뒤죽박죽" 보여서 쓰기 불편해진다.

    두 알고리즘 모두 '<' 가 아니라 '<=' 로 비교하거나,
    "오른쪽이 더 작을 때만 가져온다"는 규칙을 써서 안정성을 지킨다.
"""


def merge_sort(items, key=None):
    """병합 정렬. 새 리스트를 돌려주고 원본은 건드리지 않는다.

    원리: 반으로 쪼개고(divide), 각각 정렬한 뒤, 합친다(conquer).
         합칠 때 양쪽의 맨 앞을 비교해 작은 쪽을 가져온다.

    왜 O(n log n) 인가:
         반으로 쪼개는 깊이가 log n 이고, 각 깊이마다 전체 n개를 한 번씩
         훑으며 합치므로 n × log n.
    """
    key = key or (lambda x: x)
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left, right, key):
    """정렬된 두 리스트를 하나로 합친다."""
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        # '<=' 가 아니라 "오른쪽이 더 작을 때만 오른쪽을 가져온다"로 쓴다.
        # 동률이면 왼쪽(= 원래 앞에 있던 것)을 먼저 넣으므로 안정성이 유지된다.
        if key(right[j]) < key(left[i]):
            merged.append(right[j])
            j += 1
        else:
            merged.append(left[i])
            i += 1
    while i < len(left):
        merged.append(left[i])
        i += 1
    while j < len(right):
        merged.append(right[j])
        j += 1
    return merged


def insertion_sort(items, key=None):
    """삽입 정렬. 카드를 손에 쥐고 정렬하는 방식 그대로다.

    원리: 왼쪽은 이미 정렬돼 있다고 보고, 다음 원소를 왼쪽의 알맞은 자리에
         밀어 넣는다.

    언제 유리한가:
        이미 거의 정렬된 데이터에서는 비교만 하고 거의 안 밀어도 되므로
        O(n) 에 가까워진다. 작은 데이터에서는 병합 정렬보다 빠를 때도 있다
        (재귀 호출과 리스트 생성 비용이 없어서).
    """
    key = key or (lambda x: x)
    result = list(items)
    for i in range(1, len(result)):
        current = result[i]
        current_key = key(current)
        j = i - 1
        # 왼쪽 값이 '더 클 때만' 민다. 같으면 멈추므로 안정 정렬이 된다.
        while j >= 0 and current_key < key(result[j]):
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = current
    return result


# 기본 정렬은 병합 정렬을 쓴다(커밋 수가 늘어도 안정적으로 O(n log n)).
sort = merge_sort
