from flask import Flask, render_template

app = Flask(__name__)

correct_word = "flask"
guesses = []
num_guesses = 0


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/<string:guess>")
def wordle(guess):
    return f"{guess}"


@app.errorhandler(404) 
def invalid_route(e):
    
    # if app.url == "bad url"
    #     return

    
    return "<p>Something is wrong</p>"
