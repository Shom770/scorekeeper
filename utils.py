from collections import defaultdict
from os import environ

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = f"mongodb+srv://shayaanwadkar:{environ.get('MONGODB_PASSWORD')}@cluster0.n0wdnpf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
database = client["scorekeeper"]


def _dynamic_k_factor(games_played: int, expected_new_games: int = 10) -> float:
    """Calculates the appropriate K factor based on the elo rating."""
    return 800 / (games_played + expected_new_games)


def add_scores_to_database(
    team_one_players: list,
    team_two_players: list,
    team_one_score: int,
    team_two_score: int
) -> tuple:
    """Adds the scores for each player accordingly to the database."""
    team_one_players = sorted(name.lower().strip() for name in team_one_players)
    team_two_players = sorted(name.lower().strip() for name in team_two_players)

    scores = database["scores"]
    players = database["players"]

    winners = team_one_players if team_one_score > team_two_score else team_two_players
    current_players = {data["name"]: data["elo_rating"] for data in players.find()}

    # Add new players to the list if they exist
    for new_player in set(current_players.keys()).difference(team_one_players + team_two_players):
        players.insert_one({"name": new_player, "elo_rating": 1600})

    # Calculate new ELO ratings
    elo_of_team_one = {player: current_players[player] for player in team_one_players}
    average_elo_of_team_one = sum(elo_of_team_one.values()) / len(elo_of_team_one.values())

    elo_of_team_two = {player: current_players[player] for player in team_two_players}
    average_elo_of_team_two = sum(elo_of_team_two.values()) / len(elo_of_team_two.values())

    expected_score_of_team_one = 1 / (1 + 10 ** ((average_elo_of_team_two - average_elo_of_team_one) / 400))
    expected_score_of_team_two = 1 / (1 + 10 ** ((average_elo_of_team_one - average_elo_of_team_two) / 400))

    actual_score_of_team_one = int(team_one_score > team_two_score)
    actual_score_of_team_two = int(team_two_score > team_one_score)

    # Adjust elo accordingly for each player on team one.
    for player in team_one_players:
        games_played = scores.count_documents({"$or": [{"winners.names": player}, {"losers.names": player}]})

        new_elo_rating = (
            elo_of_team_one[player]
            + _dynamic_k_factor(games_played) * (actual_score_of_team_one - expected_score_of_team_one)
        )
        players.update_one({"name": player}, {"$set": {"name": player, "elo_rating": new_elo_rating}})

        elo_of_team_one[player] = new_elo_rating

    # Adjust elo accordingly for each player on team two.
    for player in team_two_players:
        games_played = scores.count_documents({"$or": [{"winners.names": player}, {"losers.names": player}]})

        new_elo_rating = (
            elo_of_team_two[player]
            + _dynamic_k_factor(games_played) * (actual_score_of_team_two - expected_score_of_team_two)
        )
        players.update_one({"name": player}, {"$set": {"name": player, "elo_rating": new_elo_rating}})

        elo_of_team_two[player] = new_elo_rating

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

    return (
        {name: round(elo, 0) for name, elo in elo_of_team_one.items()},
        {name: round(elo, 0) for name, elo in elo_of_team_two.items()}
    )


def get_elo_ratings() -> dict:
    return {data["name"]: data["elo_rating"] for data in database["players"].find()}


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

    records = dict(sorted(records.items(), key=lambda pair: (pair[1]["wins"], pair[1]["total_points"] / (pair[1]["wins"] + pair[1]["losses"])), reverse=True))
    return {(key[0].title(), key[1].title()): value for key, value in records.items()}


def stats_of_each_player() -> dict:
    """Retrieves the stats of each player."""
    scores = database["scores"]
    players = database["players"]
    all_players = {data["name"]: data["elo_rating"] for data in players.find()}

    records = defaultdict(lambda: {"wins": 0, "losses": 0, "total_points": 0})

    for player in set(all_players.keys()):
        games_won = list(scores.find({"winners.names": player}))
        games_lost = list(scores.find({"losers.names": player}))
        total_points = sum(
            [obj["winners"]["score"] for obj in games_won] + [obj["losers"]["score"] for obj in games_lost]
        )

        records[player]["wins"] += len(games_won)
        records[player]["losses"] += len(games_lost)
        records[player]["total_points"] += total_points
        records[player]["elo_rating"] = all_players[player]

    records = dict(sorted(records.items(), key=lambda pair: (pair[1]["elo_rating"], pair[1]["wins"], pair[1]["total_points"] / (pair[1]["wins"] + pair[1]["losses"])), reverse=True))
    return {key.title(): value for key, value in records.items()}
