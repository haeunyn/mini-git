"""커밋 그래프 알고리즘 — 위상 정렬, 최단 경로, 조상 탐색.

저장소(repository)와 분리해 둔 이유:
    이 함수들은 "커밋이 무엇인지"를 몰라도 된다. 노드와 간선만 알면 된다.
    분리해 두면 알고리즘만 따로 테스트할 수 있고, 설명할 때도 깔끔하다.

왜 커밋 그래프는 DAG(방향성 비순환 그래프)인가:
    - 방향성(Directed): 커밋은 "내 부모가 누구인지"만 안다. 부모는 자식을 모른다.
      시간이 한 방향으로만 흐르기 때문이다.
    - 비순환(Acyclic): 사이클이 생기려면 "내 조상이 내 자손"이어야 하는데,
      커밋은 만들어질 때 이미 존재하는 커밋만 부모로 삼을 수 있다.
      아직 없는 커밋을 부모로 지정할 방법이 없으므로 원리상 사이클이 불가능하다.
    - 트리가 아닌 이유: merge 커밋은 부모가 2개다. 부모가 둘이면 트리가 아니다.
"""

from .sorting import merge_sort


def topological_order(commits):
    """부모가 항상 자식보다 먼저 오도록 커밋을 나열한다 (칸 알고리즘).

    commits: {hash: Commit} 딕셔너리

    왜 '최신순 정렬'이 아니라 위상 정렬인가:
        브랜치가 갈라지면 시간순과 조상관계가 어긋날 수 있다. 예를 들어
        feature 브랜치에서 9시 15분에 커밋하고, main 으로 돌아가 9시 30분에
        커밋하면, 둘은 서로 조상 관계가 아니다. 시간만으로 줄을 세우면
        "부모보다 자식이 먼저" 나오는 경우가 생긴다.
        위상 정렬은 "의존 관계를 거스르지 않는 줄 세우기"라서 그 문제가 없다.

    칸(Kahn) 알고리즘:
        1. 각 커밋의 '남은 부모 수'(진입 차수)를 센다
        2. 부모가 0개인 커밋을 대기줄에 넣는다
        3. 하나 꺼내 출력하고, 그 자식들의 '남은 부모 수'를 1씩 줄인다
        4. 0이 된 자식을 대기줄에 넣는다 → 2번으로
        시간복잡도 O(V + E). 모든 커밋과 간선을 한 번씩만 본다.
    """
    # 1) 진입 차수 = 부모 수, 그리고 부모→자식 방향 간선을 만든다
    indegree = {}
    children = {}
    for h in commits:
        indegree[h] = 0
        children[h] = []
    for h, commit in commits.items():
        for parent in commit.parents:
            if parent in commits:
                indegree[h] += 1
                children[parent].append(h)

    # 2) 부모가 없는(= 최초) 커밋들로 시작한다.
    #    결과를 매번 똑같이 만들려고 timestamp → hash 순으로 정렬해 둔다.
    #    (sorted() 금지이므로 직접 구현한 merge_sort 를 쓴다)
    ready = [h for h in commits if indegree[h] == 0]
    ready = merge_sort(ready, key=lambda h: (commits[h].timestamp, h))

    order = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        newly_ready = []
        for child in children[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                newly_ready.append(child)
        if newly_ready:
            newly_ready = merge_sort(
                newly_ready, key=lambda h: (commits[h].timestamp, h)
            )
            ready = merge_sort(
                ready + newly_ready, key=lambda h: (commits[h].timestamp, h)
            )
    return order


def ancestors(commits, start_hash):
    """start_hash 에서 부모를 따라 도달할 수 있는 모든 커밋을 찾는다.

    자기 자신은 조상에 포함하지 않는다.
    너비 우선 탐색(BFS)으로 부모 방향만 따라간다. O(V + E).

    visited 가 필요한 이유:
        merge 커밋이 있으면 같은 조상에 두 갈래로 도달할 수 있다.
        표시해 두지 않으면 같은 커밋을 여러 번 방문하게 된다.
    """
    visited = set()
    queue = list(commits[start_hash].parents)
    while queue:
        current = queue.pop(0)
        if current in visited or current not in commits:
            continue
        visited.add(current)
        for parent in commits[current].parents:
            queue.append(parent)
    return visited


def _undirected_neighbors(commits):
    """커밋-부모 연결을 '양방향 간선'으로 바꾼 인접 목록을 만든다.

    PATH 명령의 정의가 "커밋-부모 연결을 무방향 간선으로 간주"이기 때문이다.
    조상 방향으로만 가면 형제 커밋 사이에는 길이 없지만, 양방향이면
    공통 조상을 거쳐 돌아갈 수 있다.
    """
    neighbors = {h: [] for h in commits}
    for h, commit in commits.items():
        for parent in commit.parents:
            if parent in commits:
                neighbors[h].append(parent)
                neighbors[parent].append(h)
    return neighbors


def shortest_path(commits, source, target):
    """두 커밋 사이 최단 경로(간선 수 최소). 없으면 None.

    최단 경로가 여러 개면 "hash1->hash2->... 문자열이 사전순으로 가장 작은 것".

    2단계로 푼다:
        1) target 에서 BFS 를 돌려 '모든 커밋에서 target 까지의 거리'를 구한다
        2) source 에서 출발해, 거리가 정확히 1씩 줄어드는 이웃 중
           해시가 가장 작은 것을 고르며 따라간다

    왜 이 방법이 사전순 최소를 보장하나:
        최단 경로들은 길이가 모두 같고, 커밋 해시는 전부 6자리로 길이가 같다.
        그러면 문자열 비교는 앞에서부터 한 칸씩 비교하는 것과 같아지므로,
        매 단계에서 가장 작은 해시를 고르는 '욕심쟁이 선택'이 전체 최소가 된다.
    """
    if source not in commits or target not in commits:
        return None
    if source == target:
        return [source]

    neighbors = _undirected_neighbors(commits)

    # 1) target 기준 거리 계산 (BFS 는 간선 수 기준 최단 거리를 보장한다)
    distance = {target: 0}
    queue = [target]
    while queue:
        current = queue.pop(0)
        for nxt in neighbors[current]:
            if nxt not in distance:
                distance[nxt] = distance[current] + 1
                queue.append(nxt)

    if source not in distance:
        return None  # 연결돼 있지 않다

    # 2) 거리를 1씩 줄이며, 동률이면 해시가 작은 쪽으로
    path = [source]
    current = source
    while current != target:
        candidates = [
            n for n in neighbors[current]
            if n in distance and distance[n] == distance[current] - 1
        ]
        candidates = merge_sort(candidates, key=lambda h: h)
        current = candidates[0]
        path.append(current)
    return path
