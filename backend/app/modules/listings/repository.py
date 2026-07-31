from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.schemas import ListingQuoteParams, ListingSearchParams

LATEST_PRICES_CTE = """
WITH latest_capture AS (
    SELECT room_type_id, MAX(captured_at) AS captured_at
    FROM price_snapshots
    WHERE check_in = :check_in
      AND check_out = :check_out
      AND guest_count = :guests
      AND is_available = 1
    GROUP BY room_type_id
),
current_prices AS (
    SELECT ps.*
    FROM price_snapshots ps
    JOIN latest_capture lc
      ON lc.room_type_id = ps.room_type_id
     AND lc.captured_at = ps.captured_at
    WHERE ps.check_in = :check_in
      AND ps.check_out = :check_out
      AND ps.guest_count = :guests
      AND ps.is_available = 1
)
"""


class ListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(self, params: ListingSearchParams) -> tuple[list[dict[str, Any]], int]:
        where_sql, query_params = self._search_filters(params)
        from_sql = f"""
            FROM canonical_listings c
            JOIN platform_listings pl
              ON pl.canonical_listing_id = c.id AND pl.status = 'active'
            JOIN platforms p ON p.id = pl.platform_id AND p.is_active = 1
            JOIN room_types r
              ON r.platform_listing_id = pl.id
             AND r.status = 'active'
             AND r.max_guests >= :guests
            JOIN current_prices cp ON cp.room_type_id = r.id
            WHERE c.status = 'active' {where_sql}
            GROUP BY c.id, c.public_id, c.name, c.listing_type, c.summary,
                     c.city, c.district, c.address, c.latitude, c.longitude
        """
        having_sql = self._price_filters(params, query_params)
        order_sql = {
            "price_asc": "lowest_total_amount ASC, c.id ASC",
            "price_desc": "lowest_total_amount DESC, c.id ASC",
            "rating_desc": "best_rating DESC, lowest_total_amount ASC, c.id ASC",
        }[params.sort]

        count_statement = text(
            LATEST_PRICES_CTE
            + "SELECT COUNT(*) FROM (SELECT c.id "
            + from_sql
            + having_sql
            + ") matched_listings"
        )
        total = int((await self.session.execute(count_statement, query_params)).scalar_one())

        query_params.update(
            {"limit": params.page_size, "offset": (params.page - 1) * params.page_size}
        )
        data_statement = text(
            LATEST_PRICES_CTE
            + """
            SELECT c.id, c.public_id, c.name, c.listing_type, c.summary,
                   c.city, c.district, c.address, c.latitude, c.longitude,
                   COUNT(DISTINCT p.id) AS platform_count,
                   COUNT(DISTINCT cp.id) AS offer_count,
                   MIN(cp.total_amount) AS lowest_total_amount,
                   MIN(cp.currency) AS currency,
                   MAX(pl.rating) AS best_rating
            """
            + from_sql
            + having_sql
            + f" ORDER BY {order_sql} LIMIT :limit OFFSET :offset"
        )
        rows = (await self.session.execute(data_statement, query_params)).mappings().all()
        return [dict(row) for row in rows], total

    async def get_listing(self, public_id: str) -> dict[str, Any] | None:
        statement = text(
            """
            SELECT id, public_id, name, listing_type, summary, province, city,
                   district, address, latitude, longitude
            FROM canonical_listings
            WHERE public_id = :public_id AND status = 'active'
            """
        )
        row = (
            (await self.session.execute(statement, {"public_id": public_id}))
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def get_facilities(self, listing_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        if not listing_ids:
            return {}
        statement = text(
            """
            SELECT lf.canonical_listing_id, f.code, f.name, f.category
            FROM listing_facilities lf
            JOIN facilities f ON f.id = lf.facility_id
            WHERE lf.canonical_listing_id IN :listing_ids
            ORDER BY f.category, f.code
            """
        ).bindparams(bindparam("listing_ids", expanding=True))
        rows = (await self.session.execute(statement, {"listing_ids": listing_ids})).mappings()
        result: dict[int, list[dict[str, Any]]] = {listing_id: [] for listing_id in listing_ids}
        for row in rows:
            result[int(row["canonical_listing_id"])].append(
                {"code": row["code"], "name": row["name"], "category": row["category"]}
            )
        return result

    async def get_offers(
        self,
        listing_id: int,
        params: ListingQuoteParams,
    ) -> list[dict[str, Any]]:
        statement = text(
            LATEST_PRICES_CTE
            + """
            SELECT p.code AS platform_code, p.name AS platform_name,
                   pl.name AS platform_listing_name, pl.external_id,
                   pl.rating, pl.review_count, pl.source_url,
                   r.name AS room_name, r.external_id AS room_external_id,
                   r.bed_type, r.max_guests, r.cancellation_policy,
                   cp.check_in, cp.check_out, cp.currency, cp.room_subtotal,
                   cp.cleaning_fee, cp.service_fee, cp.other_fee,
                   cp.discount_amount, cp.total_amount, cp.price_type,
                   cp.promotion_conditions, cp.remaining_units, cp.captured_at
            FROM platform_listings pl
            JOIN platforms p ON p.id = pl.platform_id AND p.is_active = 1
            JOIN room_types r
              ON r.platform_listing_id = pl.id
             AND r.status = 'active'
             AND r.max_guests >= :guests
            JOIN current_prices cp ON cp.room_type_id = r.id
            WHERE pl.canonical_listing_id = :listing_id
              AND pl.status = 'active'
            ORDER BY cp.total_amount ASC, p.code ASC, r.id ASC
            """
        )
        query_params = {
            "listing_id": listing_id,
            "check_in": params.check_in,
            "check_out": params.check_out,
            "guests": params.guests,
        }
        rows = (await self.session.execute(statement, query_params)).mappings().all()
        return [dict(row) for row in rows]

    @staticmethod
    def _search_filters(params: ListingSearchParams) -> tuple[str, dict[str, Any]]:
        filters = ["AND c.city = :city"]
        query_params: dict[str, Any] = {
            "city": params.city,
            "check_in": params.check_in,
            "check_out": params.check_out,
            "guests": params.guests,
        }
        if params.district:
            filters.append("AND c.district = :district")
            query_params["district"] = params.district
        if params.keyword:
            filters.append("AND (c.name LIKE :keyword OR c.address LIKE :keyword)")
            query_params["keyword"] = f"%{params.keyword}%"
        for index, facility_code in enumerate(params.facility):
            parameter = f"facility_{index}"
            filters.append(
                f"""AND EXISTS (
                    SELECT 1
                    FROM listing_facilities requested_lf
                    JOIN facilities requested_f ON requested_f.id = requested_lf.facility_id
                    WHERE requested_lf.canonical_listing_id = c.id
                      AND requested_f.code = :{parameter}
                )"""
            )
            query_params[parameter] = facility_code
        return " ".join(filters), query_params

    @staticmethod
    def _price_filters(params: ListingSearchParams, query_params: dict[str, Any]) -> str:
        filters: list[str] = []
        if params.min_price is not None:
            filters.append("MIN(cp.total_amount) >= :min_price")
            query_params["min_price"] = params.min_price
        if params.max_price is not None:
            filters.append("MIN(cp.total_amount) <= :max_price")
            query_params["max_price"] = params.max_price
        return " HAVING " + " AND ".join(filters) if filters else ""
