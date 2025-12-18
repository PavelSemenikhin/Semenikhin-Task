import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_event_id_unique_index(test_engine):
    async with test_engine.begin() as conn:

        def check_index(sync_conn):
            inspector = inspect(sync_conn)
            indexes = inspector.get_indexes("events")
            constraints = inspector.get_unique_constraints("events")

            unique_indexes = [i for i in indexes if i.get("unique")]
            unique_constraints = [
                c for c in constraints if "event_id" in c.get("column_names", [])
            ]
            return any("event_id" in i["column_names"] for i in unique_indexes) or bool(
                unique_constraints
            )

        result = await conn.run_sync(check_index)
        assert result, "Unique index or constraint on event_id is missing!"
