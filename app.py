from flask import Flask, render_template, request
from utils import add_scores_to_database, get_elo_ratings, stats_of_doubles_teams, stats_of_each_player

app = Flask(__name__)
latest_elo_ratings = {}


@app.route("/")
def home():
    global latest_elo_ratings

    type_of_game = request.args.get("type") or "doubles"
    section = request.args.get("section", "report_scores")
    latest_elo_ratings = get_elo_ratings()

    if section == "report_scores":
        return render_template("report_scores.html", type_of_game=type_of_game)
    elif section == "doubles_stats":
        return render_template(
            "doubles_stats.html",
            doubles_stats=enumerate(stats_of_doubles_teams().items(), start=1),
            places_to_colors={1: "yellow-600", 2: "stone-400", 3: "amber-800"}
        )
    else:
        return render_template(
            "personal_stats.html",
            personal_stats=enumerate(stats_of_each_player().items(), start=1),
            places_to_colors={1: "yellow-600", 2: "stone-400", 3: "amber-800"}
        )


@app.route("/get_elo_rating", methods=["GET"])
def get_elo_rating():
    name = request.args.get("name")
    return {"elo_rating": latest_elo_ratings.get(name, "——")}


@app.route("/process_scores", methods=["POST"])
def process_scores():
    data = request.get_json()
    if all(name for name in data["team_one_players"]) and all(name for name in data["team_two_players"]) and data["team_one_score"] >= 0 and data["team_two_score"] >= 0:
        add_scores_to_database(**data)
        return {"action": "success"}
    else:
        return {"action": "incorrect data"}


if __name__ == "__main__":
    app.run(debug=True, port=3000)