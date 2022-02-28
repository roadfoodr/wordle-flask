from flask import Flask, render_template
import random
from datetime import date
import json

app = Flask(__name__)

guesses = []
num_guesses = 0

with open("./data/w_answers.json", 'r') as f:
    w_answers = json.load(f)

with open("./data/w_allowed.json", 'r') as f:
    w_allowed = json.load(f)

# During the current day, choose the same word
rseed = int(date.today().strftime('%Y%m%d'))
random.seed(rseed)
correct_word = random.choice(w_answers)


@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/wizmode")
def wizmode():
    return correct_word

@app.route("/guess/<string:guess>")
def process_guess(guess):
    if guess == 'random':
        return random.choice(w_allowed)
    else:
        return 'guess'


@app.route("/<string:guess>")
def wordle(guess):
    return f"{guess}"


@app.errorhandler(404) 
def invalid_route(e):
        
    return "<p>Something is wrong</p>"
