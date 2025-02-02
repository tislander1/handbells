from pyabc import Tune

def abc_to_song_array(abc_song_string):
    # converts a melody in ABC format to an array format consumable by main.py
    tune1 = Tune(abc=abc_song_string)
    print(tune1.tokens)
    pitches = [item.pitch.abs_value for item in tune1.tokens if hasattr(item, 'pitch') ] 
    print('pitches:', pitches)
    x = 2

    song_array_1 = []
    for ix in range(len(tune1.tokens)):
        tok = tune1.tokens[ix]
        if 'note' in 'note' in tok.__dict__:

            note = tok.pitch.abs_value

            if tok.accidental is not None:  #fix bug with accidentals not having the right abs_value in original code
                x = 2
                if tok.accidental == '^':
                    note += 1
                elif tok.accidental == '^^':
                    note += 2
                elif tok.accidental == '_':
                    note -= 1
                elif tok.accidental == '__':
                    note -= 2
                x = 2

            duration = tok.duration
            song_array_1.append([note, duration])
        elif 'z' in tok._text:  #rest
            note = 400  #rest
            duration = float(tok.length[0])
            song_array_1.append([note, duration])
        elif ('[' in tok._text) or (']' in tok._text):  #chord or 
            if tok._text == '[':
                song_array_1.append('begin chord')
            elif tok._text == ']':
                song_array_1.append('end chord')
            elif tok._text == '[|':
                song_array_1.append('beam')
            elif tok._text == '|]':
                song_array_1.append('beam')
            elif tok._text == ']|':
                song_array_1.append('end chord')
            elif tok._text == '|[':
                song_array_1.append('begin chord')
            elif tok._text == '][':
                song_array_1.append('end chord')
                song_array_1.append('begin chord')            
            elif tok._text == ']|[':
                song_array_1.append('end chord')
                song_array_1.append('begin chord')
        song_array = []
        inside_chord = False
        for tok in song_array_1:
            if 'begin chord' in tok:
                inside_chord = True
                this_chord = []
            elif 'end chord' in tok:
                inside_chord = False
                song_array.append(this_chord)
            else:
                if not inside_chord:
                    if tok[1] == 1:
                        song_array.append(int(tok[0]))
                    else:
                        song_array.append([int(tok[0]), tok[1]])
                else:
                    this_chord.append((int(tok[0]), tok[1], 0.0))
    return song_array

with open('sound_test/facemeup.txt', 'r') as f:
#with open('sound_test/oaken-leaves-abc.txt', 'r') as f:
#with open('sound_test/valce-ardennaise.abc', 'r') as f:
    abc_lines = f.readlines()
    this_abc_song = ''.join(abc_lines)

song_array = abc_to_song_array(this_abc_song)
x = 2