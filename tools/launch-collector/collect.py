# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2.12,<3"]
# ///
# ─── How to run ───
# uv run tools/launch-collector/collect.py --help
# cd tools/launch-collector
# uv run collect.py validate examples/brand-payload.json

"""Collector CLI entry point; this foundation does not collect or write data."""

from launch_collector.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
