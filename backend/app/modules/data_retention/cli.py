import asyncio
import json

from app.db.session import async_session_factory
from app.modules.data_retention.service import DataRetentionService


async def main() -> None:
    async with async_session_factory() as session:
        report = await DataRetentionService(session).get_report()
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
