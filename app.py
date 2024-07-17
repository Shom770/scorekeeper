from flask import Flask, render_template, request
from utils import add_scores_to_database

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", type_of_game=request.args.get("type", "doubles"))


@app.route("/process_scores", methods=["POST"])
def process_scores():
    data = request.get_json()
    add_scores_to_database(**data)
    return {"action": "Scores successfully added."}


if __name__ == "__main__":
    app.run(debug=True, port=3000)