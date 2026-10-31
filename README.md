# Mini Git

코디세이 본과정 미션 **B5-2 — 파일이 언제 어떻게 바뀌었는지 기록하는 작은 프로그램 만들기**

커밋 그래프(DAG) · 위상 정렬 · BFS 최단 경로 · 역색인 · 직접 구현한 정렬을
조립해 만든 CLI 기반 Mini Git 입니다.
`sorted()` 와 `list.sort()` 를 쓰지 않았습니다.

## 실행

```bash
python main.py          # 대화형 REPL
./run.sh demo           # 데모 자동 실행 (커밋 해시 고정)
./run.sh test           # 테스트 27개
./run.sh check          # 제약 준수 검사
./run.sh bench          # 정렬 성능 비교 (보너스 3)
```

Python 3.10 이상이면 되고, 외부 패키지는 쓰지 않습니다.

```
$ python main.py
mini-git> init "Alice"
Initialized repository.
Current branch: main
Current user: Alice
mini-git> commit "Initial commit"
[main cf8dab] Initial commit
mini-git> exit
```

## 명령어

| 분류 | 명령어 | 설명 |
|---|---|---|
| 저장소·브랜치 | `INIT <user_name>` | 초기화, main 브랜치 생성 |
| | `BRANCH <name>` | 현재 HEAD 를 가리키는 새 브랜치 |
| | `SWITCH <name>` | HEAD 이동 |
| | `COMMIT <message>` | 현재 HEAD 를 부모로 새 커밋 |
| 로그·탐색 | `LOG` | **부모가 자식보다 먼저** (위상 정렬) |
| | `LOG --sort-by=date\|author` | 직접 구현한 병합 정렬 |
| | `PATH <c1> <c2>` | 최단 경로. 없으면 `No path` |
| | `ANCESTORS <hash>` | 모든 조상 |
| 검색 | `SEARCH <keyword>` | 역색인 기반 |
| | `SEARCH --author=<name>` | 역색인 기반 |
| 보너스 | `MERGE <branch>` | 부모 2개인 merge 커밋 |
| | `DIFF <file1> <file2>` | LCS 기반 줄 단위 비교 |
| 편의 | `STATUS` | 현재 상태 요약 |

명령어는 **대소문자를 구분하지 않습니다**. 공백이 든 인자는 따옴표로 감쌉니다.

에러 표준: `Invalid args`, `Unknown branch: <name>`, `Unknown commit: <hash>`

## 동작 예시

```
mini-git> log
commit cf8dab (Alice, 2026-01-01 00:00:01)
    Initial commit
commit 3faa7b (Alice, 2026-01-01 00:00:02) [feature]
    Add login feature
commit e18585 (Alice, 2026-01-01 00:00:03) [main]
    Add payment feature

mini-git> path 3faa7b e18585      ← 형제 커밋. 공통 조상을 거쳐 돌아간다
Path: 3faa7b -> cf8dab -> e18585

mini-git> search login             ← 전체 훑지 않고 역색인에서 바로
Found 1 commit(s):
- 3faa7b: Add login feature
```

## 구조

```
main.py                 엔트리 포인트
minigit/
├── commit.py           커밋 노드 + 해시 생성
├── repository.py       커밋 그래프 · 브랜치 · HEAD 상태
├── graph.py            위상 정렬 · BFS 최단 경로 · 조상 탐색
├── sorting.py          병합 정렬 · 삽입 정렬 (직접 구현)
├── index.py            역색인 (keyword / author)
├── diff.py             LCS 기반 diff (보너스 1)
├── parser.py           토큰 분리 · 옵션 파싱
├── commands.py         명령어 실행 · 출력 형식
├── cli.py              REPL
└── errors.py           에러 메시지 표준
tools/
├── check_constraints.py  제약 준수 자동 검사
└── benchmark_sort.py     정렬 성능 비교 (보너스 3)
```

알고리즘 설명은 **[docs/ALGORITHMS.md](docs/ALGORITHMS.md)** 에 정리했습니다.

## 핵심 아이디어 세 가지

**1. 브랜치는 커밋 묶음이 아니라 "이름표"다**

`repository.py` 의 `_branches` 는 `{브랜치이름: 커밋해시}` 입니다. 브랜치를
만드는 건 **이름표 하나 더 붙이는 것**이라 비용이 거의 0입니다. 커밋하면
그 이름표만 새 커밋으로 옮겨 가고, HEAD 는 "지금 어느 이름표 위에 서 있는가"입니다.

**2. LOG 는 최신순이 아니라 위상 정렬이다**

브랜치가 갈라지면 시간순과 조상관계가 어긋납니다. 위상 정렬은 "의존 관계를
거스르지 않는 줄 세우기"라서 **부모가 항상 자식보다 먼저** 나옵니다.

**3. 역색인이 빠른 이유는 방향을 뒤집었기 때문이다**

커밋→단어를 단어→커밋으로 뒤집으면, 검색이 `O(N × L)` 에서 `O(1) + O(K)` 가
됩니다. 커밋이 1만 개여도 "login"이 든 3개만 꺼냅니다.

## 테스트

```bash
./run.sh test
```

```
Ran 27 tests in 0.001s
OK
```

타임스탬프는 가짜 시계를 주입해 1초씩 증가시킵니다. 그래야 커밋 해시와 정렬
결과가 매번 같아져 검증할 수 있습니다.

## 제약 사항 준수

| 요구 | 지킨 방법 |
|---|---|
| `sorted()` · `list.sort()` 금지 | `merge_sort` · `insertion_sort` 직접 구현 |
| 그래프 전용 라이브러리 금지 | `graph.py` 에 BFS·위상정렬 직접 구현 |
| 커밋 해시 세션 내 유일 | 내용 + 카운터 해시, 충돌 시 재생성 |
| 알고리즘을 독립 모듈로 분리 | `graph.py` · `sorting.py` · `index.py` |
| 역색인 2종 이상 | keyword, author |
| 파일 추적 · 네트워크 · 영속성 미구현 | 커밋 메타데이터 중심, 메모리 동작 |

```bash
./run.sh check
```

```
검사 대상: 파이썬 파일 12개 (minigit/ + main.py)
금지 항목: sorted(), .sort(), 그래프 전용 라이브러리
  위반 없음
✅ 표준 정렬 API와 그래프 라이브러리를 사용하지 않았습니다.
```

`grep` 대신 `ast` 모듈로 구문 트리를 읽어 검사합니다. 문자열 검색은
`merge_sort(...)` 안의 `sort` 까지 잡아내 정확하지 않기 때문입니다.
