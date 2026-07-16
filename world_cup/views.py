from django.db import connections
from django.db.models import F, Sum
from django.shortcuts import render

from .models import Match


def _get_collection():
    conn = connections['default']
    conn.ensure_connection()
    return conn.get_collection("world_cup_match")


def tournament_goals(request):
    """Pipeline 1 — built-in aggregate: total goals across completed matches."""
    result = (
        Match.objects.filter(ft_score1__isnull=False)
        .annotate(total_goals=F("ft_score1") + F("ft_score2"))
        .aggregate(tournament_goals=Sum("total_goals"))
    )
    return render(request, "world_cup/goals.html", {
        "total_goals": result["tournament_goals"] or 0,
    })


def top_scorers(request):
    """Pipeline 2 — raw_aggregate: leaderboard via $unwind + $group."""
    pipeline = [
        {"$project": {"goals": {"$concatArrays": ["$goals1", "$goals2"]}}},
        {"$unwind": "$goals"},
        {"$match": {"goals.own_goal": {"$ne": True}}},
        {"$group": {"_id": "$goals.name", "total_goals": {"$sum": 1}}},
        {"$sort": {"total_goals": -1}},
        {"$limit": 10},
    ]
    collection = _get_collection()
    results = list(collection.aggregate(pipeline))
    scorers = [{"name": r["_id"], "goals": r["total_goals"]} for r in results]
    return render(request, "world_cup/scorers.html", {"scorers": scorers})


ALLOWED_QUERIES = {
    "team": {
        "description": "All matches for a team",
        "example": "team France",
    },
    "round": {
        "description": "Matches in a round (e.g. round Quarter-final)",
        "example": "round Quarter-final",
    },
    "top scorers": {
        "description": "Top 10 scorers via $unwind + $group pipeline",
        "example": "top scorers",
    },
    "goals by round": {
        "description": "Goals per round via $group pipeline",
        "example": "goals by round",
    },
    "goals": {
        "description": "Total tournament goals",
        "example": "goals",
    },
}


def _execute_query(query_text):
    """Parse and execute a user query, return result dict."""
    q = query_text.strip().lower()

    if q == "goals":
        result = (
            Match.objects.filter(ft_score1__isnull=False)
            .annotate(total_goals=F("ft_score1") + F("ft_score2"))
            .aggregate(tournament_goals=Sum("total_goals"))
        )
        return {
            "query": "db.world_cup_match.aggregate([{$match: {ft_score1: {$ne: null}}}, {$addFields: {total_goals: {$add: ['$ft_score1', '$ft_score2']}}}, {$group: {_id: null, tournament_goals: {$sum: '$total_goals'}}}])",
            "results": [{"tournament_goals": result["tournament_goals"] or 0}],
        }

    if q in ("top scorers", "scorers", "top"):
        pipeline = [
            {"$project": {"goals": {"$concatArrays": ["$goals1", "$goals2"]}}},
            {"$unwind": "$goals"},
            {"$match": {"goals.own_goal": {"$ne": True}}},
            {"$group": {"_id": "$goals.name", "total_goals": {"$sum": 1}}},
            {"$sort": {"total_goals": -1}},
            {"$limit": 10},
        ]
        collection = _get_collection()
        results = list(collection.aggregate(pipeline))
        return {
            "query": "db.world_cup_match.aggregate([{$project: {goals: {$concatArrays: ['$goals1', '$goals2']}}}, {$unwind: '$goals'}, {$match: {'goals.own_goal': {$ne: true}}}, {$group: {_id: '$goals.name', total_goals: {$sum: 1}}}, {$sort: {total_goals: -1}}, {$limit: 10}])",
            "results": [{"scorer": r["_id"], "goals": r["total_goals"]} for r in results],
        }

    if q.startswith("team "):
        team = query_text.strip()[5:].strip()
        from django.db.models import Q
        matches = Match.objects.filter(Q(team1__iexact=team) | Q(team2__iexact=team)).order_by("date")
        return {
            "query": f'db.world_cup_match.aggregate([{{$match: {{$or: [{{team1: {{$regex: "^{team}$", $options: "i"}}}}, {{team2: {{$regex: "^{team}$", $options: "i"}}}}]}}}}, {{$sort: {{date: 1}}}}])',
            "results": [
                {
                    "date": str(m.date),
                    "round": m.round,
                    "team1": m.team1,
                    "team2": m.team2,
                    "score": f"{m.ft_score1}-{m.ft_score2}" if m.ft_score1 is not None else "TBD",
                }
                for m in matches
            ],
        }

    if q.startswith("round "):
        round_name = query_text.strip()[6:].strip()
        matches = Match.objects.filter(round__icontains=round_name).order_by("date")
        return {
            "query": f'db.world_cup_match.aggregate([{{$match: {{round: {{$regex: "{round_name}", $options: "i"}}}}}}, {{$sort: {{date: 1}}}}])',
            "results": [
                {
                    "date": str(m.date),
                    "team1": m.team1,
                    "team2": m.team2,
                    "score": f"{m.ft_score1}-{m.ft_score2}" if m.ft_score1 is not None else "TBD",
                }
                for m in matches
            ],
        }

    if q in ("goals by round", "goals per round"):
        pipeline = [
            {"$match": {"ft_score1": {"$ne": None}}},
            {"$group": {
                "_id": "$round",
                "total_goals": {"$sum": {"$add": ["$ft_score1", "$ft_score2"]}},
                "matches": {"$sum": 1},
            }},
            {"$sort": {"total_goals": -1}},
        ]
        collection = _get_collection()
        results = list(collection.aggregate(pipeline))
        return {
            "query": "db.world_cup_match.aggregate([{$match: {ft_score1: {$ne: null}}}, {$group: {_id: '$round', total_goals: {$sum: {$add: ['$ft_score1', '$ft_score2']}}, matches: {$sum: 1}}}, {$sort: {total_goals: -1}}])",
            "results": [{"round": r["_id"], "goals": r["total_goals"], "matches": r["matches"]} for r in results],
        }

    return None


def query_shell(request):
    """Interactive query shell — form POST triggers full page reload for MQL panel."""
    context: dict = {"queries": ALLOWED_QUERIES}

    if request.method == "POST":
        query_text = request.POST.get("query", "").strip()
        context["last_query"] = query_text

        if query_text:
            result = _execute_query(query_text)
            if result is None:
                context["error"] = f"Unknown query. Try: {', '.join(ALLOWED_QUERIES.keys())}"
            else:
                context["mongo_query"] = result.get("query", "")
                context["results"] = result.get("results", [])

    return render(request, "world_cup/shell.html", context)