from __future__ import annotations

import json

from .data_store import DefectDataStore


def main() -> None:
    store = DefectDataStore()
    summary = store.get_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
