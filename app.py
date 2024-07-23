from flask import Flask, render_template, request
from utils import (
    add_scores_to_database,
    connect_to_database,
    client,
    get_elo_ratings,
    stats_of_doubles_teams,
    stats_of_each_player
)

app = Flask(__name__)
latest_elo_ratings = {}


@app.route("/")
def home():
    type_of_game = request.args.get("type") or "doubles"
    return render_template("index.html", type_of_game=type_of_game)


@app.route("/personal_stats")
def personal_stats():
    if client is None:
        connect_to_database()

    return render_template(
        "personal_stats.html",
        personal_stats=enumerate(stats_of_each_player().items(), start=1),
        places_to_colors={1: "yellow-600", 2: "stone-400", 3: "amber-800"}
    )


@app.route("/doubles_stats")
def doubles_stats():
    if client is None:
        connect_to_database()

    return render_template(
        "doubles_stats.html",
        doubles_stats=enumerate(stats_of_doubles_teams().items(), start=1),
        places_to_colors={1: "yellow-600", 2: "stone-400", 3: "amber-800"}
    )


@app.route("/get_elo_rating", methods=["GET"])
def get_elo_rating():
    global latest_elo_ratings

    if client is None:
        connect_to_database()

    if not latest_elo_ratings:
        latest_elo_ratings = get_elo_ratings()

    name = request.args.get("name")
    return {"elo_rating": round(latest_elo_ratings.get(name, 0), 0) or "——"}


@app.route("/process_scores", methods=["POST"])
def process_scores():
    global latest_elo_ratings

    if client is None:
        connect_to_database()

    data = request.get_json()

    if (
        all(name for name in data["team_one_players"])
        and all(name for name in data["team_two_players"])
        and data["team_one_score"] >= 0 and data["team_two_score"] >= 0
        and not (data["team_one_score"] == 0 and data["team_two_score"] == 0)
        and not (data["team_one_score"] >= 20 and data["team_two_score"] >= 20)
    ):
        elo_of_team_one, elo_of_team_two = add_scores_to_database(**data)
        latest_elo_ratings = get_elo_ratings()

        return {"action": "success", "elo_of_team_one": elo_of_team_one, "elo_of_team_two": elo_of_team_two}
    else:
        return {"action": "incorrect data"}


if __name__ == "__main__":
    app.run(debug=True, port=3000)
