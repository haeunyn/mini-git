"""보너스 3 — 정렬 알고리즘 성능 비교.

병합 정렬 O(n log n) 과 삽입 정렬 O(n²) 이 입력 크기에 따라 어떻게 벌어지는지
직접 재어 본다. "O(n²)이 느리다"를 말로만 아는 것과 숫자로 보는 것은 다르다.

사용법:  python3 tools/benchmark_sort.py
"""

import random
import sys
import time
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from minigit.sorting import insertion_sort, merge_sort  # noqa: E402

SIZES = (100, 500, 1000, 2000, 4000)


def measure(fn, data) -> float:
    start = time.perf_counter()
    fn(data)
    return time.perf_counter() - start


def main() -> None:
    random.seed(42)  # 매번 같은 입력 → 결과를 비교할 수 있다

    print("정렬 알고리즘 성능 비교 (무작위 정수)")
    print(f"{'크기':>6} | {'병합 정렬':>12} | {'삽입 정렬':>12} | {'배수':>8}")
    print("-" * 52)
    for n in SIZES:
        data = [random.randint(0, 10_000) for _ in range(n)]
        t_merge = measure(merge_sort, data)
        t_insert = measure(insertion_sort, data)
        ratio = t_insert / t_merge if t_merge else 0
        print(f"{n:>6} | {t_merge*1000:>9.2f}ms | {t_insert*1000:>9.2f}ms | {ratio:>7.1f}x")

    print()
    print("이미 정렬된 입력 (삽입 정렬의 최선 케이스)")
    print(f"{'크기':>6} | {'병합 정렬':>12} | {'삽입 정렬':>12} | {'배수':>8}")
    print("-" * 52)
    for n in SIZES:
        data = list(range(n))
        t_merge = measure(merge_sort, data)
        t_insert = measure(insertion_sort, data)
        ratio = t_insert / t_merge if t_merge else 0
        print(f"{n:>6} | {t_merge*1000:>9.2f}ms | {t_insert*1000:>9.2f}ms | {ratio:>7.1f}x")

    print()
    print("해석")
    print("  무작위 입력 : 크기가 2배가 되면 삽입 정렬은 약 4배 느려진다(n²).")
    print("               병합 정렬은 2배 조금 넘게만 느려진다(n log n).")
    print("  정렬된 입력 : 삽입 정렬은 밀 일이 없어 O(n)에 가까워져 역전된다.")
    print("               '최악 복잡도만 보고 고르면 안 된다'는 예시다.")


if __name__ == "__main__":
    main()
