import numpy as np
import os

character_index = {}

def load_character_index():
    files = [f for f in os.listdir() if f[-4:] == ".csv"]
    for file in files:
        data = open(f"{file}", "r").read()
        data = [[[255., 255., 255.] if c == '1' else [0., 0., 0.] for c in line.split(',')] for line in data.split("\n")]
        character_index[chr(int(file[5:-4]))] = (np.array(data), len(data[0]), len(data))

def put_text(frame, text: str, start):
    cursor = start
    for c in text:
        letter = character_index[c]
        frame[cursor[0]:cursor[0]+letter[2], cursor[1]:cursor[1]+letter[1]] = letter[0]
        cursor[1] += letter[1]+1
