import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory, engine
from app.modules.listings.models import (
    CanonicalListing,
    Facility,
    ListingFacility,
    PlatformListing,
    RoomType,
)
from app.modules.platforms.models import Platform
from app.modules.pricing.models import PriceSnapshot

PLATFORMS = [
    {"code": "meituan", "name": "美团", "base_url": "https://www.meituan.com"},
    {"code": "tujia", "name": "途家", "base_url": "https://www.tujia.com"},
    {"code": "muniao", "name": "木鸟民宿", "base_url": "https://www.muniao.com"},
]

FACILITIES = [
    {"code": "wifi", "name": "无线网络", "category": "基础设施"},
    {"code": "kitchen", "name": "厨房", "category": "生活设施"},
    {"code": "washer", "name": "洗衣机", "category": "生活设施"},
    {"code": "air_conditioning", "name": "空调", "category": "基础设施"},
    {"code": "parking", "name": "停车位", "category": "交通设施"},
    {"code": "projector", "name": "投影设备", "category": "娱乐设施"},
    {"code": "ground_floor", "name": "一楼房型", "category": "无障碍"},
    {"code": "sea_view", "name": "海景", "category": "景观"},
]

LISTINGS = [
    {
        "public_id": "DL_000001",
        "name": "云栖·洱海庭院民宿",
        "listing_type": "homestay",
        "summary": "靠近才村码头的安静庭院，适合情侣与小家庭。",
        "province": "云南省",
        "city": "大理市",
        "district": "大理镇",
        "address": "才村村委会月华路示范地址1号",
        "latitude": Decimal("25.7072310"),
        "longitude": Decimal("100.1798420"),
        "facilities": ["wifi", "kitchen", "washer", "air_conditioning", "projector"],
    },
    {
        "public_id": "DL_000002",
        "name": "苍山慢居庭院",
        "listing_type": "homestay",
        "summary": "位于古城生活区，步行餐饮便利，并提供适合老人的一楼房型。",
        "province": "云南省",
        "city": "大理市",
        "district": "大理镇",
        "address": "古城人民路示范地址18号",
        "latitude": Decimal("25.6939210"),
        "longitude": Decimal("100.1648330"),
        "facilities": ["wifi", "kitchen", "air_conditioning", "parking", "ground_floor"],
    },
    {
        "public_id": "DL_000003",
        "name": "月白·双廊海景民宿",
        "listing_type": "guesthouse",
        "summary": "临近洱海的景观住宿，适合重视日出与海景的旅行者。",
        "province": "云南省",
        "city": "大理市",
        "district": "双廊镇",
        "address": "双廊村环海路示范地址6号",
        "latitude": Decimal("25.9084410"),
        "longitude": Decimal("100.1937270"),
        "facilities": ["wifi", "air_conditioning", "projector", "sea_view"],
    },
]

PLATFORM_LISTINGS = [
    ("DL_000001", "meituan", "MT-DL-1001", "大理云栖洱海庭院民宿", "4.83", 328),
    ("DL_000001", "tujia", "TJ-DL-2101", "云栖·洱海设计师庭院", "4.78", 415),
    ("DL_000001", "muniao", "MN-DL-3101", "才村码头云栖庭院民宿", "4.76", 186),
    ("DL_000002", "meituan", "MT-DL-1002", "苍山慢居庭院客栈", "4.72", 264),
    ("DL_000002", "tujia", "TJ-DL-2102", "大理古城苍山慢居", "4.81", 301),
    ("DL_000003", "tujia", "TJ-DL-2103", "月白双廊一线海景民宿", "4.86", 522),
    ("DL_000003", "muniao", "MN-DL-3103", "双廊月白海景美宿", "4.79", 209),
]

ROOMS = [
    ("meituan", "MT-DL-1001", "MT-R-101", "庭院大床房", "32.00", "1张1.8米大床", 2, "庭院"),
    ("tujia", "TJ-DL-2101", "TJ-R-201", "庭院景观大床房", "33.00", "1张1.8米大床", 2, "庭院"),
    ("tujia", "TJ-DL-2101", "TJ-R-202", "露台家庭房", "46.00", "1张大床和1张单人床", 3, "山景"),
    ("muniao", "MN-DL-3101", "MN-R-301", "近洱海庭院大床房", "31.00", "1张1.8米大床", 2, "庭院"),
    ("meituan", "MT-DL-1002", "MT-R-102", "一楼舒适双床房", "36.00", "2张1.2米单人床", 2, "庭院"),
    ("tujia", "TJ-DL-2102", "TJ-R-203", "古城一楼双床房", "35.00", "2张1.2米单人床", 2, "庭院"),
    ("tujia", "TJ-DL-2103", "TJ-R-204", "日出海景大床房", "38.00", "1张1.8米大床", 2, "海景"),
    ("muniao", "MN-DL-3103", "MN-R-302", "临海阳台大床房", "37.00", "1张1.8米大床", 2, "海景"),
]

PRICES = [
    (
        "meituan",
        "MT-DL-1001",
        "MT-R-101",
        "1287.00",
        "0.00",
        "45.00",
        "0.00",
        "30.00",
        "1302.00",
        "member",
        "需美团会员",
    ),
    (
        "tujia",
        "TJ-DL-2101",
        "TJ-R-201",
        "1320.00",
        "50.00",
        "30.00",
        "0.00",
        "0.00",
        "1400.00",
        "standard",
        None,
    ),
    (
        "tujia",
        "TJ-DL-2101",
        "TJ-R-202",
        "1680.00",
        "50.00",
        "35.00",
        "0.00",
        "80.00",
        "1685.00",
        "promotion",
        "连续入住3晚优惠",
    ),
    (
        "muniao",
        "MN-DL-3101",
        "MN-R-301",
        "1260.00",
        "60.00",
        "30.00",
        "0.00",
        "40.00",
        "1310.00",
        "new_user",
        "仅限新用户",
    ),
    (
        "meituan",
        "MT-DL-1002",
        "MT-R-102",
        "1110.00",
        "0.00",
        "36.00",
        "0.00",
        "0.00",
        "1146.00",
        "standard",
        None,
    ),
    (
        "tujia",
        "TJ-DL-2102",
        "TJ-R-203",
        "1164.00",
        "40.00",
        "28.00",
        "0.00",
        "60.00",
        "1172.00",
        "promotion",
        "国庆早订优惠",
    ),
    (
        "tujia",
        "TJ-DL-2103",
        "TJ-R-204",
        "2070.00",
        "60.00",
        "40.00",
        "0.00",
        "100.00",
        "2070.00",
        "promotion",
        "连续入住优惠",
    ),
    (
        "muniao",
        "MN-DL-3103",
        "MN-R-302",
        "1980.00",
        "80.00",
        "35.00",
        "0.00",
        "70.00",
        "2025.00",
        "new_user",
        "仅限新用户",
    ),
]


async def upsert_by(
    session: AsyncSession,
    model: type[Any],
    lookup: dict[str, Any],
    values: dict[str, Any],
) -> Any:
    instance = await session.scalar(select(model).filter_by(**lookup))
    if instance is None:
        instance = model(**lookup, **values)
        session.add(instance)
    else:
        for field, value in values.items():
            setattr(instance, field, value)
    await session.flush()
    return instance


async def seed_demo_data() -> dict[str, int]:
    async with async_session_factory() as session:
        platform_by_code: dict[str, Platform] = {}
        for data in PLATFORMS:
            platform = await upsert_by(
                session,
                Platform,
                {"code": data["code"]},
                {"name": data["name"], "base_url": data["base_url"], "is_active": True},
            )
            platform_by_code[platform.code] = platform

        facility_by_code: dict[str, Facility] = {}
        for data in FACILITIES:
            facility = await upsert_by(
                session,
                Facility,
                {"code": data["code"]},
                {"name": data["name"], "category": data["category"]},
            )
            facility_by_code[facility.code] = facility

        listing_by_public_id: dict[str, CanonicalListing] = {}
        for data in LISTINGS:
            values = {
                key: value for key, value in data.items() if key not in {"public_id", "facilities"}
            }
            values["status"] = "active"
            listing = await upsert_by(
                session,
                CanonicalListing,
                {"public_id": data["public_id"]},
                values,
            )
            listing_by_public_id[listing.public_id] = listing
            for facility_code in data["facilities"]:
                await upsert_by(
                    session,
                    ListingFacility,
                    {
                        "canonical_listing_id": listing.id,
                        "facility_id": facility_by_code[facility_code].id,
                    },
                    {"source": "demo"},
                )

        platform_listing_by_key: dict[tuple[str, str], PlatformListing] = {}
        synced_at = datetime(2026, 7, 31, 12, 0, 0)
        for public_id, platform_code, external_id, name, rating, review_count in PLATFORM_LISTINGS:
            platform = platform_by_code[platform_code]
            listing = listing_by_public_id[public_id]
            platform_listing = await upsert_by(
                session,
                PlatformListing,
                {"platform_id": platform.id, "external_id": external_id},
                {
                    "canonical_listing_id": listing.id,
                    "name": name,
                    "address": listing.address,
                    "rating": Decimal(rating),
                    "review_count": review_count,
                    "source_url": f"https://demo.stay-scale.local/{platform_code}/{external_id}",
                    "status": "active",
                    "last_synced_at": synced_at,
                },
            )
            platform_listing_by_key[(platform_code, external_id)] = platform_listing

        room_by_key: dict[tuple[str, str, str], RoomType] = {}
        for (
            platform_code,
            listing_external_id,
            room_external_id,
            name,
            area,
            bed_type,
            guests,
            view,
        ) in ROOMS:
            platform_listing = platform_listing_by_key[(platform_code, listing_external_id)]
            room = await upsert_by(
                session,
                RoomType,
                {"platform_listing_id": platform_listing.id, "external_id": room_external_id},
                {
                    "name": name,
                    "area_m2": Decimal(area),
                    "bed_type": bed_type,
                    "bed_count": 2 if "2张" in bed_type or "和" in bed_type else 1,
                    "max_guests": guests,
                    "is_entire_unit": True,
                    "has_private_bathroom": True,
                    "view_type": view,
                    "cancellation_policy": "入住前24小时可免费取消",
                    "status": "active",
                },
            )
            room_by_key[(platform_code, listing_external_id, room_external_id)] = room

        captured_at = datetime(2026, 7, 31, 12, 0, 0)
        for price in PRICES:
            (
                platform_code,
                listing_external_id,
                room_external_id,
                room_subtotal,
                cleaning_fee,
                service_fee,
                other_fee,
                discount_amount,
                total_amount,
                price_type,
                conditions,
            ) = price
            room = room_by_key[(platform_code, listing_external_id, room_external_id)]
            await upsert_by(
                session,
                PriceSnapshot,
                {
                    "room_type_id": room.id,
                    "check_in": date(2026, 10, 2),
                    "check_out": date(2026, 10, 5),
                    "guest_count": 2,
                    "captured_at": captured_at,
                    "price_type": price_type,
                },
                {
                    "currency": "CNY",
                    "room_subtotal": Decimal(room_subtotal),
                    "cleaning_fee": Decimal(cleaning_fee),
                    "service_fee": Decimal(service_fee),
                    "other_fee": Decimal(other_fee),
                    "discount_amount": Decimal(discount_amount),
                    "total_amount": Decimal(total_amount),
                    "promotion_conditions": conditions,
                    "is_available": True,
                    "remaining_units": 2,
                },
            )

        await session.commit()

        models = [Platform, CanonicalListing, PlatformListing, RoomType, Facility, PriceSnapshot]
        return {
            model.__tablename__: int(
                await session.scalar(select(func.count()).select_from(model)) or 0
            )
            for model in models
        }


async def main() -> None:
    try:
        counts = await seed_demo_data()
        print("Demo data is ready:")
        for table, count in counts.items():
            print(f"  {table}: {count}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
