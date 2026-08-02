import argparse
import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.db.session import async_session_factory, engine
from app.modules.review_analysis.schemas import ReviewAnalysisRequest
from app.modules.review_analysis.service import ReviewAnalysisService


class ReviewImportBatch(BaseModel):
    listing_public_id: str = Field(min_length=1, max_length=32)
    request: ReviewAnalysisRequest


class ReviewImportFixture(BaseModel):
    batches: list[ReviewImportBatch] = Field(min_length=1, max_length=100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import and analyze normalized review data")
    parser.add_argument("--fixture", required=True, type=Path, help="UTF-8 JSON fixture path")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    fixture = ReviewImportFixture.model_validate_json(args.fixture.read_text(encoding="utf-8"))
    imported = []
    async with async_session_factory() as session:
        service = ReviewAnalysisService(session)
        for batch in fixture.batches:
            result = await service.analyze(batch.listing_public_id, batch.request)
            if result is None:
                raise ValueError(f"Listing not found: {batch.listing_public_id}")
            imported.append(
                {
                    "listing_public_id": batch.listing_public_id,
                    "analysis_id": result.analysis_id,
                    "review_count": result.review_count,
                    "provider": result.provider,
                }
            )
    print(json.dumps({"imported": imported}, ensure_ascii=False, indent=2))


async def main() -> None:
    try:
        await run()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
