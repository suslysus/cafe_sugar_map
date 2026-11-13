# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pydantic>=2.12,<3", "anyio>=4.14,<5",
#   "httpx2[http2,brotli,zstd]>=2.16,<3", "selectolax>=1,<2",
# ]
# ///
# ─── How to run ───
# uv run tools/launch-collector/collect.py --help
# cd tools/launch-collector
# uv run collect.py validate examples/brand-payload.json

"""Collector CLI: input validation and explicit local Paik collection, without DB access."""

from launch_collector.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
