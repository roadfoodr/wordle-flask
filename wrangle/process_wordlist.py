# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 01:07:42 2022

@author: MDP
"""

import pandas as pd
import json


url = "https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/5d752e5f0702da315298a6bb5a771586d6ff445c/wordle-answers-alphabetical.txt"
df = pd.read_csv(url, header=None)
w_answers = list(df[0])

url = "https://gist.githubusercontent.com/cfreshman/cdcdf777450c5b5301e439061d29694c/raw/de1df631b45492e0974f7affe266ec36fed736eb/wordle-allowed-guesses.txt"
df2 = pd.read_csv(url, header=None)
w_allowed = list(df2[0])


# change working directory to location of this file
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

with open("w_answers.json", 'w') as f:
    # indent=2 is not needed but makes the file human-readable
    json.dump(w_answers, f, indent=2) 

with open("w_allowed.json", 'w') as f:
    # indent=2 is not needed but makes the file human-readable
    json.dump(w_allowed, f, indent=2) 

# to read back in
# with open("file.json", 'r') as f:
#     file_contents = json.load(f)


