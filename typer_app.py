import typer
import csv
import json
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import time
from app.db.base import AsyncPostgresqlSessionLocal
from app.db.models import Event

app = typer.Typer()
cli = typer.Typer()
app.add_typer(cli, name="import")


def parse_row(row: dict) -> dict:
    """Convert CSV row into Python types ready for DB insert."""
    try:
        event_id = uuid.UUID(row["event_id"])
        occurred_at = datetime.fromisoformat(row["occurred_at"])
        user_id = int(row["user_id"])
        event_type = row["event_type"]
        properties = json.loads(row["properties_json"])
        return {
            "event_id": event_id,
            "occurred_at": occurred_at,
            "user_id": user_id,
            "event_type": event_type,
            "properties": properties,
        }
    except Exception as e:
        typer.echo(f"Error parsing row: {e}")
        return None


async def import_to_db(parsed_rows: list[dict]):
    """Insert parsed events into the database asynchronously."""
    typer.echo("Connecting to database...")

    async with AsyncPostgresqlSessionLocal() as session:
        inserted, skipped = 0, 0
        for row in parsed_rows:
            event = Event(**row)
            session.add(event)
            try:
                await session.commit()
                inserted += 1
            except IntegrityError:
                await session.rollback()
                skipped += 1
            except Exception as e:
                await session.rollback()
                typer.echo(f"Unexpected DB error: {e}")
        typer.echo(f"Done. Inserted: {inserted}, Skipped (duplicates): {skipped}")


@cli.command("events")
def import_events(csv_path: str):
    """Import events from a CSV file into the database."""
    typer.echo(f"Reading file: {csv_path}")
    start = time.time()
    try:
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            parsed_rows = []
            for row in reader:
                parsed = parse_row(row)
                if parsed:
                    parsed_rows.append(parsed)
        typer.echo(f"Parsed {len(parsed_rows)} rows successfully.")
        asyncio.run(import_to_db(parsed_rows))
    except FileNotFoundError:
        typer.echo("File not found. Check the path.")
    except Exception as e:
        typer.echo(f"Error while reading CSV: {e}")
    finally:
        typer.echo(f"Benchmark finished in {time.time() - start:.2f} seconds.")


if __name__ == "__main__":
    app()
