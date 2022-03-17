from flask import Flask, request, render_template
import random
from datetime import date
import json
import string
# import sys

app = Flask(__name__)

MAX_GUESSES = 6

turns = []
guesses_remaining = MAX_GUESSES
gamestate = 'pending'
letter_result_map = {letter:'' for letter in string.ascii_lowercase}


with open("./data/w_answers.json", 'r') as f:
    w_answers = json.load(f)

with open("./data/w_allowed.json", 'r') as f:
    w_allowed = json.load(f)
game_commands = ['random', 'wizmode']
w_allowed = list(set(w_answers + w_allowed + game_commands))

# During the current day, choose the same word
rseed = int(date.today().strftime('%Y%m%d'))
random.seed(rseed)
correct_word = random.choice(w_answers)


@app.route("/")
@app.route("/guess", methods=['GET'])
def hello_world():
    return render_template("wordle.html", turns=turns, 
                           guesses_remaining = guesses_remaining,
                           letter_result_map=letter_result_map,
                           gamestate='pending')

@app.route("/wizmode")
def wizmode():
    results = evaluate_guess(correct_word, correct_word, False)
    extra_tiles = zip(correct_word, results)
    return render_template("wordle.html", turns=turns, extra_tiles=extra_tiles, 
                           guesses_remaining=guesses_remaining,
                           letter_result_map=letter_result_map,
                           gamestate='pending')
    
@app.route("/guess", methods=['POST'])
def process_guess():
    global guesses_remaining
    guess = request.form['submit-guess'].lower()
    
    error_message = ''
    if guess not in w_allowed:
        error_message = 'Not an allowable guess:'

    if not guess:
         error_message = 'Please submit a guess'
       
    past_guesses = []
    for past_turn in turns:
        past_guess = "".join(letter for letter, past_result in past_turn)
        past_guesses.append(past_guess)            
    if guess in past_guesses:
        error_message = 'Word previously guessed:'
       
    if error_message:
        results = ['tbd' for letter in guess]
        extra_tiles = zip(guess, results)
        return render_template("wordle.html", turns=turns, extra_tiles=extra_tiles, 
                           guesses_remaining=guesses_remaining,
                           letter_result_map=letter_result_map,
                           error_message=error_message,
                           gamestate='pending')
    
    if guess == 'wizmode':
        return wizmode()
    
    if guess == 'random':
        guess = random.choice(w_allowed)
        
    results = evaluate_guess(correct_word, guess)
    # Convert to list because Jinja not able to work easily with zip iterator
    new_tiles = list(zip(guess, results))  
    turns.append(new_tiles)
    guesses_remaining -= 1
    return render_template("wordle.html", turns=turns, 
                       guesses_remaining=guesses_remaining,
                       letter_result_map=letter_result_map,
                       gamestate='pending')


@app.errorhandler(404)
def invalid_route(e):
    return "<p>Something is wrong</p>"


def evaluate_guess(correct_word: str, guess: str, update_map: bool=True) -> list:
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
        if update_map:
            # issue: result in map could be "downgraded" from correct to present
            letter_result_map[c] = result
    return results
