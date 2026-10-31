#!/usr/bin/env python3
"""Mini Git 엔트리 포인트.

실행:  python main.py
       python main.py --demo   (커밋 해시가 항상 같게 나오는 데모 모드)
"""

import sys

from minigit.cli import run

if __name__ == "__main__":
    sys.exit(run(deterministic="--demo" in sys.argv))
