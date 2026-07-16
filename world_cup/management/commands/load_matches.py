# world_cup/management/commands/load_matches.py
import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from world_cup.models import Goal, Match

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "worldcup_2026.json"


def build_goals(raw_goals):
    return [
        Goal(
            name=g["name"],
            minute=g["minute"],
            penalty=g.get("penalty", False),
            own_goal=g.get("owngoal", False),
        )
        for g in raw_goals
    ]


def to_match_kwargs(raw_match):
    score = raw_match.get("score", {})
    ft = score.get("ft", [None, None])
    ht = score.get("ht", [None, None])
    et = score.get("et", [None, None])
    p = score.get("p", [None, None])

    return dict(
        num=raw_match.get("num"),
        round=raw_match["round"],
        date=datetime.strptime(raw_match["date"], "%Y-%m-%d").date(),
        kickoff_time=raw_match["time"],
        group=raw_match.get("group", ""),
        ground=raw_match["ground"],
        team1=raw_match["team1"],
        team2=raw_match["team2"],
        ft_score1=ft[0],
        ft_score2=ft[1],
        ht_score1=ht[0],
        ht_score2=ht[1],
        et_score1=et[0],
        et_score2=et[1],
        pen_score1=p[0],
        pen_score2=p[1],
        goals1=build_goals(raw_match.get("goals1", [])),
        goals2=build_goals(raw_match.get("goals2", [])),
    )


class Command(BaseCommand):
    help = (
        "Load the curated World Cup 2026 matches (Groups A, B, I, J) into MongoDB. "
        "Source: worldcup_data/worldcup_2026.json — 24 matches total, "
        "16 completed with real goals, 8 unplayed (Matchday 14/17)."
    )

    def handle(self, *args, **options):
        with open(DATA_FILE) as f:
            raw_matches = json.load(f)["matches"]

        self.stdout.write(f"Found {len(raw_matches)} matches to load.")

        batch_size = 5
        created = 0
        for i in range(0, len(raw_matches), batch_size):
            batch = raw_matches[i : i + batch_size]
            Match.objects.bulk_create([Match(**to_match_kwargs(m)) for m in batch])
            created += len(batch)
            self.stdout.write(f"Loaded {created}/{len(raw_matches)} matches...")

        self.stdout.write(self.style.SUCCESS(f"Done: {created} matches loaded."))