#!/usr/bin/env bash
# Mini Git 실행 도우미
#   ./run.sh          대화형 REPL
#   ./run.sh demo     데모 스크립트 자동 실행 (커밋 해시 고정)
#   ./run.sh test     테스트 전체 실행
#   ./run.sh check    제약 사항(sorted/.sort 미사용) 검사
#   ./run.sh bench    정렬 알고리즘 성능 비교 (보너스 3)
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}

case "${1:-repl}" in
  repl)  exec "$PY" main.py ;;
  demo)  "$PY" main.py --demo < demo/demo.txt ;;
  test)  "$PY" -m unittest discover -s tests -t . -v ;;
  check) "$PY" -I tools/check_constraints.py ;;
  bench) "$PY" -I tools/benchmark_sort.py ;;
  *)     echo "사용법: ./run.sh [repl|demo|test|check|bench]" >&2; exit 1 ;;
esac
