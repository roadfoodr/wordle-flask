from flask import (
    Flask, flash, make_response, redirect, render_template, 
    request, session, url_for
    )
import random
from datetime import date, datetime
import json
import string
import os
# import sys

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev')

MAX_GUESSES = 6


with open("./data/w_answers.json", 'r') as f:
    w_answers = json.load(f)

with open("./data/w_allowed.json", 'r') as f:
    w_allowed = json.load(f)
game_commands = ['newgame', 'random', 'wizmode']
w_allowed = list(set(w_answers + w_allowed))
entries_allowed = list(set(game_commands + w_allowed))


@app.before_request 
def initialize_session(): 
    if not session:
        session['turns'] = []
        session['guesses_remaining'] = MAX_GUESSES
        session['gamestate'] = 'pending'
        session['letter_result_map'] = {letter:'' for letter in string.ascii_lowercase}
        # During the current day, choose the same word each time
        rseed = int(date.today().strftime('%Y%m%d'))
        random.seed(rseed)
        session['correct_word'] = random.choice(w_answers)
        # reset seed so different players don't get the same sequence
        random.seed(random.seed(datetime.now()))


@app.route("/")
# @app.route("/guess", methods=['GET'])
def index():
    return render_template("wordle.html")

@app.route("/session")
def show_session():
    return session

@app.route("/newgame")
def newgame():
    session.clear()
    return redirect(url_for('index'))

@app.route("/wizmode")
def wizmode():
    results = evaluate_guess(session['correct_word'], 
                             session['correct_word'], False)
    flash('The secret word is:', 'user_message')
    flash(list(zip(session['correct_word'], results)), 'extra_tiles')
    return redirect(url_for('index'))
    
@app.route("/guess", methods=['POST'])
def process_guess():
    guess = request.form['submit-guess'].lower()

    if guess == 'newgame':
        return newgame()
    
    if guess == 'wizmode':
        return wizmode()

    if guess == 'random':
        guess = random.choice(w_allowed)
    
    if guess and guess not in entries_allowed:
        flash('Not an allowable guess:', 'user_message')

    if not guess:
        flash('Please submit a guess', 'user_message')

    past_guesses = []
    for past_turn in session['turns']:
        past_guess = "".join(letter for letter, past_result in past_turn)
        past_guesses.append(past_guess)            
    if guess in past_guesses:
        flash('Word previously guessed:', 'user_message')

    if session.get('_flashes'):  # there has been an error message
        results = ['tbd' for letter in guess]
        flash(list(zip(guess, results)), 'extra_tiles')
    else:
        results = evaluate_guess(session['correct_word'], guess)
        new_tiles = list(zip(guess, results))  
        session['turns'].append(new_tiles)
        session['guesses_remaining'] -= 1
        
    return redirect(url_for('index'))


@app.errorhandler(404)
def invalid_route(e):
    return make_response("<p>Something is wrong</p>", 404)


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
            session['letter_result_map'][c] = result
    return results


