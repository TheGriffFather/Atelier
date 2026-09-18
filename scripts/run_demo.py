"""Run Atelier with a separate synthetic catalogue, without credentials.

Usage: python scripts/run_demo.py [--port 8779] [--seed-only]
A marked local/demo folder is reused; existing unmarked data is never replaced.
"""

import argparse
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = "atelier-synthetic-demo-v1"


def prepare_directory(directory: Path) -> None:
    marker = directory / ".atelier-demo"
    if directory.exists() and any(directory.iterdir()):
        if not marker.is_file() or marker.read_text().strip() != MARKER:
            raise SystemExit("Refusing to use a non-demo directory. Choose a clean checkout.")
    directory.mkdir(parents=True, exist_ok=True)
    marker.write_text(MARKER + "\n")


def configure(directory: Path) -> None:
    # Relative mail/biography paths also resolve inside the isolated demo folder.
    os.chdir(directory)
    os.environ.update(
        {
            "DEMO_MODE": "true",
            "DATABASE_URL": "sqlite+aiosqlite:///" + (directory / "catalogue.db").as_posix(),
            "DATA_DIR": str(directory),
            "IMAGE_DIR": str(directory / "images/artworks"),
            "ENABLE_SCHEDULER": "false",
            "DEBUG": "false",
            "SMTP_HOST": "",
            "SMTP_USERNAME": "",
            "SMTP_PASSWORD": "",
            "NOTIFICATION_EMAIL": "",
            "EBAY_CLIENT_ID": "",
            "EBAY_CLIENT_SECRET": "",
            "PERPLEXITY_API_KEY": "",
        }
    )


def seed(directory: Path) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from src.database.models import (
        Base,
        Artist,
        Artwork,
        ArtworkImage,
        Exhibition,
        ArtworkExhibition,
        Contact,
        Outreach,
        ResearchLead,
        SavedSearch,
        AlertResult,
        DisplaySettings,
    )
    from demo_art import make_study

    database = directory / "catalogue.db"
    if database.exists():
        print("Reusing the existing synthetic demo catalogue.")
        return
    engine = create_engine("sqlite:///" + database.as_posix())
    Base.metadata.create_all(engine)
    titles = [
        "Sun over the inlet",
        "Woven currents",
        "The ochre arch",
        "Botanical night",
        "Four quiet orbits",
        "Objects at noon",
        "Terracotta coast",
        "Tidal rhythm",
        "A room for light",
        "The olive branch",
        "Intervals in blue",
        "Still, together",
        "At the horizon",
        "Lines of the estuary",
        "Passage in gold",
        "Evening garden",
    ]
    years = [
        2024,
        2024,
        2023,
        2023,
        2022,
        2022,
        2021,
        2021,
        2020,
        2020,
        2019,
        2019,
        2018,
        2018,
        2017,
        2017,
    ]
    today = datetime.now(timezone.utc).replace(
        tzinfo=None, hour=10, minute=0, second=0, microsecond=0
    )
    with Session(engine) as s:
        artist = Artist(
            name="Atelier Studio",
            specialty="Original digital colour studies",
            biography="Synthetic demonstration collection; no real artist is represented.",
        )
        s.add(artist)
        s.flush()
        works = []
        for i, title in enumerate(titles):
            work = Artwork(
                title=title,
                description=(
                    "An original procedural colour study exploring balanced forms, quiet texture, "
                    "and the relationship between warm pigment and deep blue. "
                    "Created for the Atelier demo; all catalogue details below are synthetic."
                ),
                source_platform="manual",
                source_url=f"https://example.org/atelier/study-{i + 1:02}",
                year_created=years[i],
                medium="Digital pigment study",
                art_type="Digital Art",
                dimensions="40 × 50 cm",
                dimensions_cm="40 × 50",
                category="Still Life",
                subject_matter="Abstract geometry and imagined landscapes",
                signed="Atelier Studio · demonstration",
                is_verified=i < 12,
                confidence_score=0.96 if i < 12 else 0.72,
                acquisition_status=["acquired", "watching", "contacted", "new"][i % 4],
                price=320 + i * 45,
                estimated_value=380 + i * 45,
                currency="USD",
                date_found=today - timedelta(days=i * 2),
                provenance="Synthetic record: Studio archive → Sample Collection, 2024.",
                exhibition_history="Colour / Form / Quiet · Example Gallery (sample exhibition)",
                condition="Demo condition record: excellent, unframed digital study.",
                research_status="complete" if i < 12 else "unverified",
                current_location="Sample Collection",
                last_known_owner="Demo archive",
                is_personal_collection=i % 4 == 0,
                notes="Sample data only. No real sale, valuation, or attribution.",
                research_notes="Compare the study image with its synthetic exhibition entry.",
            )
            s.add(work)
            s.flush()
            works.append(work)
            image_path = directory / "images/artworks" / str(work.id) / "study.jpg"
            w, h = make_study(image_path, i)
            s.add(
                ArtworkImage(
                    artwork_id=work.id,
                    url=f"/api/images/{work.id}/study.jpg",
                    local_path=f"images/artworks/{work.id}/study.jpg",
                    is_primary=True,
                    width=w,
                    height=h,
                    date_downloaded=today,
                )
            )
        show_specs = [
            ("Colour / Form / Quiet", "Example Gallery", 2024, [0, 1, 2, 3]),
            ("The Shape of Stillness", "Sample Museum", 2022, [4, 5, 6, 7]),
            ("Studies in Blue", "Demo Project Space", 2020, [8, 9, 10, 11]),
            ("First Impressions", "Example Print Room", 2018, [12, 13, 14, 15]),
        ]
        for title, venue, year, indices in show_specs:
            show = Exhibition(
                artist_id=artist.id,
                title=title,
                venue_name=venue,
                year=year,
                venue_city="Sample City",
                exhibition_type="gallery",
                is_solo=True,
                start_date=datetime(year, 5, 1),
                end_date=datetime(year, 7, 15),
                description="Synthetic exhibition for demonstrating linked catalogue records.",
                source_url="https://example.org/exhibitions",
            )
            s.add(show)
            s.flush()
            for index in indices:
                s.add(ArtworkExhibition(artwork_id=works[index].id, exhibition_id=show.id))
        for i, (name, kind, subject, status) in enumerate(
            [
                (
                    "Example Gallery",
                    "gallery",
                    "Installation photographs for Colour / Form / Quiet",
                    "responded",
                ),
                (
                    "Sample Museum",
                    "museum",
                    "Confirm catalogue dimensions for Four quiet orbits",
                    "awaiting_response",
                ),
                (
                    "Demo Print Archive",
                    "educational",
                    "Locate an early proof of At the horizon",
                    "follow_up_needed",
                ),
                ("Example Collection", "individual", "Provenance note for The ochre arch", "draft"),
            ]
        ):
            contact = Contact(
                name=name,
                organization=name,
                contact_type=kind,
                email=f"archive{i + 1}@example.org",
                website="https://example.org",
                role="Sample catalogue contact",
                connection_notes="Fictional contact used only in this demonstration.",
                priority=4 - i % 3,
            )
            s.add(contact)
            s.flush()
            s.add(
                Outreach(
                    contact_id=contact.id,
                    subject=subject,
                    status=status,
                    content="Synthetic correspondence example. No message was sent.",
                    date_sent=today - timedelta(days=7 - i) if status != "draft" else None,
                    follow_up_date=today + timedelta(days=i + 1),
                    response_received=status == "responded",
                    response_summary="Sample reply: archive images supplied for catalogue review."
                    if status == "responded"
                    else None,
                    requesting_images=i == 0,
                    requesting_metadata=i == 1,
                    requesting_provenance=i == 3,
                    notes="Demonstration record only; not actual correspondence.",
                )
            )
        for title, priority, status, category in [
            (
                "Match the early coastal study to a catalogue entry",
                "high",
                "investigating",
                "provenance",
            ),
            ("Locate a higher-resolution installation image", "medium", "contacted", "exhibition"),
            ("Check the edition notes for Intervals in blue", "medium", "new", "publication"),
        ]:
            s.add(
                ResearchLead(
                    title=title,
                    priority=priority,
                    status=status,
                    category=category,
                    description="Synthetic research lead for demonstrating catalogue follow-through.",
                    next_action="Compare the sample archive note with the linked work.",
                    source="Demo collection",
                )
            )
        for i, name in enumerate(
            ["Coastal studies", "Architectural forms", "Colour and still life"]
        ):
            search = SavedSearch(
                name=name,
                query=f"Atelier Studio {name.lower()}",
                platform="ebay",
                is_active=True,
                last_run=today - timedelta(hours=3),
                total_results=4,
                new_since_last_view=2,
                min_price=100,
                max_price=1500,
                notes="Synthetic saved search; live scanning is disabled.",
            )
            s.add(search)
            s.flush()
            for j in range(4):
                index = i * 4 + j
                s.add(
                    AlertResult(
                        search_id=search.id,
                        title=titles[index],
                        price=320 + index * 45,
                        source_url=f"https://example.org/demo-listing/{index + 1}",
                        seller_name="Sample listing archive",
                        image_url=f"/api/images/{works[index].id}/study.jpg",
                        date_found=today - timedelta(hours=j + 3),
                        status=["new", "confirmed", "watching", "reviewing"][j],
                        confidence_score=0.89,
                        description="Synthetic discovery result. No marketplace search was performed.",
                    )
                )
        s.add(
            DisplaySettings(
                frame_style="black",
                interval=3600,
                shuffle=False,
                show_title=True,
                verified_only=True,
                image_fit="contain",
            )
        )
        s.commit()
    engine.dispose()
    print(
        "Created 16 original studies, 4 exhibitions, 4 sample contacts, and synthetic research records."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8779)
    parser.add_argument("--seed-only", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose a port between 1024 and 65535.")
    directory = ROOT / "local/demo"
    prepare_directory(directory)
    sys.path.insert(0, str(ROOT))
    configure(directory)
    seed(directory)
    if not args.seed_only:
        import uvicorn

        print(f"Atelier demo: http://127.0.0.1:{args.port}/?tab=gallery")
        uvicorn.run("src.api.main:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
