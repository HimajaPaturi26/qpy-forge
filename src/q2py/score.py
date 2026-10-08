"""Print the measured holdout report."""

from __future__ import annotations

import json

from q2py.metrics import measure


def main() -> None:
    report = measure("holdout")
    public = {key: value for key, value in report.items() if key != "rows"}
    print(json.dumps(public, indent=2))


if __name__ == "__main__":
    main()
