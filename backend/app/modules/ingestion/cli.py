import argparse
import asyncio
import json
from pathlib import Path

from app.db.session import async_session_factory, engine
from app.modules.ingestion.adapters import FixturePlatformAdapter
from app.modules.ingestion.service import IngestionService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import normalized platform listing data")
    parser.add_argument("--platform", required=True, help="Platform code configured in MySQL")
    parser.add_argument("--fixture", required=True, type=Path, help="UTF-8 JSON fixture path")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    adapter = FixturePlatformAdapter(args.platform, args.fixture)
    async with async_session_factory() as session:
        summary = await IngestionService(session).import_from(adapter)
    print(json.dumps(summary.model_dump(), ensure_ascii=False, indent=2))


async def main() -> None:
    try:
        await run()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
