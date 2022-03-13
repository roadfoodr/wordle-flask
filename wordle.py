from flask import Flask, render_template
import random
from datetime import date
import json
# import sys

app = Flask(__name__)

MAX_GUESSES = 6

turns = []
guesses_remaining = MAX_GUESSES
letters_used = set()
gamestate = 'pending'


with open("./data/w_answers.json", 'r') as f:
    w_answers = json.load(f)

with open("./data/w_allowed.json", 'r') as f:
    w_allowed = json.load(f)
w_allowed = list(set(w_answers + w_allowed + ['random']))

# During the current day, choose the same word
rseed = int(date.today().strftime('%Y%m%d'))
random.seed(rseed)
correct_word = random.choice(w_answers)


@app.route("/")
def hello_world():
    return render_template("index.html", turns=turns, tiles=[], 
                           guesses_remaining = guesses_remaining,
                           valid=True, gamestate='pending')

@app.route("/wizmode")
def wizmode():
    results = evaluate_guess(correct_word, correct_word)
    tiles = zip(correct_word, results)
    return render_template("index.html", turns=turns, tiles=tiles, 
                           guesses_remaining=guesses_remaining,
                           letters_used=letters_used,
                           valid=True, gamestate='pending')

@app.route("/guess/<string:guess>")
def process_guess(guess):
    global guesses_remaining
    guess=guess.lower()
    if guess not in w_allowed:
        results = ['tbd' for letter in guess]
        tiles = zip(guess, results)
        return render_template("index.html", turns=turns, tiles=tiles, 
                           guesses_remaining=guesses_remaining,
                           letters_used=letters_used,
                           valid=False, gamestate='pending')
    if guess == 'random':
        guess = random.choice(w_allowed)
        
    # TODO: if the guess is repeated, don't increment histories
    # TODO: sort letters used
    results = evaluate_guess(correct_word, guess)
    tiles = list(zip(guess, results))  # Jinja not able to work easily with zip iterator
    turns.append(tiles)
    letters_used.update(set(guess))
    guesses_remaining -= 1
    return render_template("index.html", turns=turns[:-1], tiles=turns[-1], 
                       guesses_remaining=guesses_remaining,
                       letters_used=letters_used,
                       valid=True, gamestate='pending')


@app.errorhandler(404) 
def invalid_route(e):
    return "<p>Something is wrong</p>"


def evaluate_guess(correct_word: str, guess: str) -> list:
    if len(correct_word) != len(guess):
        return None
    results = []
    for i, c in enumerate(guess):
        result = 'absent'
        if c in correct_word:
            result = 'present'
        if c == correct_word[i]:
            result = 'correct'
        results.append(result)
    return results
