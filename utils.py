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
    scores = database["scores"]
    winners = team_one_players if team_one_score > team_two_score else team_two_players

    for player in team_one_players:
        scores.insert_one({
            "name": player.lower(),
            "score": team_one_score,
            "won_game": player in winners
        })

    for player in team_two_players:
        scores.insert_one({
            "name": player.lower(),
            "score": team_two_score,
            "won_game": player in winners
        })
