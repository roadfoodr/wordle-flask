from flask import (
    Flask, flash, make_response, redirect, render_template,
    request, session, url_for
    )
import random
from datetime import date, datetime
import json
import string
import os
import re
import sys

app = Flask(__name__)
app.app_context().push()
app.secret_key = os.environ.get('SECRET_KEY', 'dev')
GA_TRACKING_ID = os.environ.get('GA_TRACKING_ID', 'dev')
# print(GA_TRACKING_ID, file=sys.stdout)
# sys.stdout.flush()
@app.context_processor
def inject_global_vars():
    return {'GA_TRACKING_ID': GA_TRACKING_ID}


MAX_GUESSES = 6
CSS_ABSENT, CSS_PRESENT, CSS_CORRECT = 'absent', 'present', 'correct'
CSS_UNKNOWN, CSS_HINT = 'tbd', 'hint'


with open("./data/w_answers.json", 'r') as f:
    w_answers = json.load(f)
with open("./data/w_allowed.json", 'r') as f:
    w_allowed = json.load(f)
game_commands = {'restart': "Restart the game with today's secret word", 
                 'newgame': 'Restart the game with a random new secret word',
                 'newword': 'Follow by <word> to restart with a specified secret word', 
                 'random': 'Submit a random guess from all allowable guesses', 
                 'hint': 'Display some words that match information known so far',
                 'auto': 'Submit a random guess consistent with information known so far',
                 'wizmode': 'Temporarily reveal the current secret word',
                 'help': 'Display this list of game commands'
                 }
w_allowed = list(set(w_answers + w_allowed))
entries_allowed = list(set(w_allowed + list(game_commands)))

WORD_LENGTH = len(random.choice(w_answers))

@app.before_request 
def initialize_session(): 
    if not session:
        session['turns'] = []
        session['guesses_remaining'] = MAX_GUESSES
        session['gamestate'] = 'in-progress'
        session['game_commands'] = game_commands
        session['letter_result_map'] = {letter:'' for letter in string.ascii_lowercase}
        # During the current day, choose the same word each time
        session['letter_position_include_list'] = list('.' * WORD_LENGTH)
        session['letter_position_exclude_list'] = [[] for _ in range(WORD_LENGTH)]
        rseed = int(date.today().strftime('%Y%m%d'))
        random.seed(rseed)
        session['correct_word'] = random.choice(w_answers)
        # reset global seed so different players don't get the same sequence
        random.seed(random.seed(datetime.now()))

@app.route("/")
def index():
    return render_template("wordle.html")

@app.route("/restart")
def restart():
    session.clear()
    return redirect(url_for('index'))

@app.route("/newgame")
def newgame():
    session.clear()
    initialize_session()
    random.seed(random.seed(datetime.now()))
    session['correct_word'] = random.choice(w_answers)
    return redirect(url_for('index'))

@app.route("/newword/<new_word>")
def newword(new_word=''):
    new_word = new_word.lower()
    if new_word not in w_answers:
        if new_word:
            flash('Not an allowable secret word:', 'user_message')
            results = [CSS_UNKNOWN for letter in new_word]
            flash(list(zip(new_word, results)), 'extra_tiles')
        else:
            flash('You must supply a secret word', 'user_message')
    else:
        session.clear()
        initialize_session()
        session['correct_word'] = new_word
    return redirect(url_for('index'))

@app.route("/hint")
def hint():
    numhints, selected_hints = identify_hints()
    num_selected = len(selected_hints)
    possibility_verb = 'is' if num_selected == 1 else 'are'
    possibility_noun = 'possibility' if num_selected == 1 else 'possibilities'
    include_string = ', including' if numhints > num_selected else ''
    flash(f'There {possibility_verb} {numhints} {possibility_noun}{include_string}:', 
          'user_message')
    
    for hint in selected_hints:
        results = [CSS_HINT for letter in hint]
        flash(list(zip(hint, results)), 'extra_tiles')
    return redirect(url_for('index'))

@app.route("/wizmode")
def wizmode():
    flash('The secret word is:', 'user_message')
    results = [CSS_UNKNOWN for letter in session['correct_word']]
    flash(list(zip(session['correct_word'], results)), 'extra_tiles')
    return redirect(url_for('index'))
    
@app.route("/guess", methods=['POST'])
def process_guess():
    guess = request.form['submit-guess'].lower()

    if guess == 'restart':
        return restart()
    
    if guess == 'newgame':
        return newgame()

    if guess.startswith('newword'):
        guess = guess.removeprefix('newword')  # requires Python 3.9
        # only keep alpha characters
        guess = "".join(c for c in guess if c.isalpha())
        return newword(guess)

    if guess == 'wizmode':
        return wizmode()

    if guess == 'help':
        return redirect(url_for('index', _anchor="help"))
    
    if session['gamestate'] == 'in-progress':

        if guess == 'hint':
            return hint()

        if guess == 'random':
            guess = random.choice(w_allowed)    

        if guess == 'auto':
            numhints, selected_hints = identify_hints()
            guess = random.choice(selected_hints)    

        if guess and guess not in entries_allowed:
            flash('Not an allowable guess:', 'user_message')
    
        if not guess:
            flash('Please submit a guess or game command (try HELP)', 'user_message')
            return redirect(url_for('index'))
    
        past_guesses = []
        for past_turn in session['turns']:
            past_guess = "".join(letter for letter, past_result in past_turn)
            past_guesses.append(past_guess)            
        if guess in past_guesses:
            flash('Word previously guessed:', 'user_message')
    
        if session.get('_flashes'):  # there has been a user message
            results = [CSS_UNKNOWN for letter in guess]
            flash(list(zip(guess, results)), 'extra_tiles')
        else:
            results = evaluate_guess(session['correct_word'], guess)
            new_tiles = list(zip(guess, results))  
            session['turns'].append(new_tiles)
            session['guesses_remaining'] -= 1
            if guess == session['correct_word']:
                session['gamestate'] = 'success'
            elif session['guesses_remaining'] < 1:
                session['gamestate'] = 'failure'
                flash('The correct word was:', 'user_message')
                results = [CSS_UNKNOWN for letter in guess]
                flash(list(zip(session['correct_word'], results)), 'extra_tiles')
    else:
        flash('Only game commands may be submitted now (try HELP)', 'user_message')

    return redirect(url_for('index'))


@app.route("/admin/session")
def show_session():
    # extract the raw values from the SecureCookieSession object
    session_dict = {key: val for key, val in session.items()}
    return session_dict

@app.route("/admin/clearsession")
def clear_session():
    session.clear()
    return('session cleared')
    

@app.errorhandler(404)
def invalid_route(e):
    return make_response("<h3>No matching route</h3>", 404)


def evaluate_guess(correct_word: str, guess: str, update_maps: bool=True) -> list:
    '''
    Given a correct word and a guess to evaluate against it, return a list of
    strings describing the presence or absence of letters from guess in the
    correct word.  Strings correspond to css classes used by the front end to
    visually display results.  Optionally record these results in the user session.
    '''
    if len(correct_word) != len(guess):
        raise ValueError("correct_word and guess must have matching lengths")
    results = []
    for i, char in enumerate(guess):
        result = CSS_ABSENT
        if char == correct_word[i]:
            result = CSS_CORRECT
            if update_maps:
                session['letter_position_include_list'][i] = char
        elif char in correct_word:
            result = CSS_PRESENT
            if update_maps:
                session['letter_position_exclude_list'][i].append(char)
        results.append(result)
        if update_maps:
            # don't "downgrade" letters we previously saw as correct
            if session['letter_result_map'][char] != CSS_CORRECT:
                session['letter_result_map'][char] = result
    return results


def identify_hints(max_results=10):
    '''
    From user session, obtain the secret (correct) word and information about 
    correct, present, absent letters known so far in the game.  Return the
    number and (length-limited) list of possible answers consistent with known
    info.
    '''
    # letters known to be in certain positions
    correct_r = re.compile("".join(session['letter_position_include_list']))
    hints = list(filter(correct_r.match, w_answers))
    
    # letters known not to be in certain positions
    exclude_r_string = ''.join(
        ['[^'+''.join(position_list)+']' if position_list
         else '.'
         for position_list in session['letter_position_exclude_list']]
        )
    exclude_r = re.compile(exclude_r_string)
    hints = list(filter(exclude_r.match, hints))

    # letters known to be present in word
    present_letters = [letter for letter, result 
                       in session['letter_result_map'].items()
                       if result == CSS_PRESENT]
    for letter in present_letters:
        hints = list(filter(lambda x: (letter in x), hints))

    # letters known not to be present in word
    absent_letters = [letter for letter, result 
                       in session['letter_result_map'].items()
                       if result == CSS_ABSENT]
    for letter in absent_letters:
        hints = list(filter(lambda x: (letter not in x), hints))
    
    num_hints = len(hints)
    sampled_hints = random.sample(hints, min(num_hints, max_results))
        
    return (num_hints, sampled_hints)
