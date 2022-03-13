from flask import Flask, render_template
import random
from datetime import date
import json

app = Flask(__name__)

MAX_GUESSES = 5

guesses = []
results_history = []
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
    return render_template("index.html", guess='')

@app.route("/wizmode")
def wizmode():
    # return f"Today's word: <strong>{correct_word}</strong>"
    results = evaluate_guess(correct_word, correct_word)
    tiles = zip(correct_word, results)
    return render_template("index.html", tiles=tiles, valid=True)

@app.route("/guess/<string:guess>")
def process_guess(guess):
    guess=guess.lower()
    if guess == 'random':
        # return (f'A random allowable guess: <strong>'
        #        f'{random.choice(w_allowed)}</strong>')]
        guess = random.choice(w_allowed)
        results = evaluate_guess(correct_word, guess)
        tiles = zip(guess, results)
        return render_template("index.html", tiles=tiles, valid=True)
        
    if guess not in w_allowed:
        results = ['tbd' for letter in guess]
        tiles = zip(guess, results)
        # return f'<strong>{guess}</strong> is not an allowable guess'
        return render_template("index.html", tiles=tiles, valid=False)
    # TODO: if the guess is repeated, don't increment histories
    # TODO: continue here to implement display of current and past guesses
    # evaluate 
    else:
        results = evaluate_guess(correct_word, guess)
        letters_used.update(set(guess))
        guesses.append(guess)
        results_history.append(results)
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
        result = 'absent'
        if c in correct_word:
            result = 'present'
        if c == correct_word[i]:
            result = 'correct'
        results.append(result)
    return results
    
