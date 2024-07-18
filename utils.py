from collections import defaultdict
from os import environ

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = f"mongodb+srv://shayaanwadkar:{environ.get('MONGODB_PASSWORD')}@cluster0.n0wdnpf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
database = client["scorekeeper"]


def add_scores_to_database(
    team_one_players: list,
    team_two_players: list,
    team_one_score: int,
    team_two_score: int
) -> None:
    """Adds the scores for each player accordingly to the database."""
    team_one_players = sorted(name.lower() for name in team_one_players)
    team_two_players = sorted(name.lower() for name in team_two_players)

    scores = database["scores"]
    players = database["players"]

    winners = team_one_players if team_one_score > team_two_score else team_two_players
    current_players = players.find()[0]["all_players"]

    # Add new players to the list if they exist
    players.update_one(
        {"all_players": current_players},
        {"$set": {"all_players": list(set(current_players).union(team_one_players + team_two_players))}}
    )

    # Insert scores
    scores.insert_one({
        "winners": {
            "names": winners,
            "score": max(team_one_score, team_two_score)
        },
        "losers": {
            "names": team_one_players if team_two_players == winners else team_two_players,
            "score": min(team_one_score, team_two_score)
        }
    })


def stats_of_doubles_teams() -> dict:
    """Retrieves the stats of all teams that have played."""
    scores = database["scores"]
    records = defaultdict(lambda: {"wins": 0, "losses": 0, "total_points": 0})

    for game in list(scores.find()):
        if len(game["winners"]["names"]) != 2 and len(game["losers"]["names"]) != 2:
            continue

        records[tuple(game["winners"]["names"])]["wins"] += 1
        records[tuple(game["winners"]["names"])]["total_points"] += game["winners"]["score"]

        records[tuple(game["losers"]["names"])]["losses"] += 1
        records[tuple(game["losers"]["names"])]["total_points"] += game["losers"]["score"]

    records = dict(sorted(records.items(), key=lambda pair: pair[1]["wins"], reverse=True))
    return {(key[0].title(), key[1].title()): value for key, value in records.items()}