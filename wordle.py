from flask import Flask, render_template
import random
from datetime import date
import json

app = Flask(__name__)

MAX_GUESSES = 5

guesses = []
num_guesses = 0
letters_used = set()

with open("./data/w_answers.json", 'r') as f:
    w_answers = json.load(f)

with open("./data/w_allowed.json", 'r') as f:
    w_allowed = json.load(f)
w_allowed = list(set(w_answers + w_allowed))

# During the current day, choose the same word
rseed = int(date.today().strftime('%Y%m%d'))
random.seed(rseed)
correct_word = random.choice(w_answers)


@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/wizmode")
def wizmode():
    return f"Today's word: <strong>{correct_word}</strong>"

@app.route("/guess/<string:guess>")
def process_guess(guess):
    guess=guess.lower()
    if guess == 'random':
        return (f'A random allowable guess: <strong>'
               f'{random.choice(w_allowed)}</strong>')
    if guess not in w_allowed:
        return f'<strong>{guess}</strong> is not an allowable guess'
    else:
        results = evaluate_guess(correct_word, guess)
        letters_used.update(set(guess))
        guesses.append(guess)
        # Use len(guesses) to track the number of guesses
        return (f'You guessed: <strong>{guess}</strong>\n'
                f'the results are: {results}\n'
                f'letters used: {letters_used}')



@app.errorhandler(404) 
def invalid_route(e):
        
    return "<p>Something is wrong</p>"


def evaluate_guess(correct_word: str, guess: str) -> list:
    if len(correct_word) != len(guess):
        return None
    results = []
    for i, c in enumerate(guess):
        result = 'not_in'
        if c in correct_word:
            result = 'in_word'
        if c == correct_word[i]:
            result = 'in_place'
        results.append(result)
    return results
    
