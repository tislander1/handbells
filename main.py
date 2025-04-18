import librosa
import soundfile
import numpy as np
from pyabc import Tune
from datetime import datetime

def abc_to_song_array(abc_song_string):
    # converts a melody in ABC format to an array format consumable by main.py
    tune1 = Tune(abc=abc_song_string)

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
            note = 'rest'  #rest
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
                        if isinstance(tok[0], str):
                            song_array.append([tok[0], tok[1]])
                        else:
                            song_array.append([int(tok[0]), tok[1]])
                else:
                    this_chord.append((int(tok[0]), tok[1], 0.0))
    return [song_array]

def add_new_note(song, note, sample_idx):
    if sample_idx > len(song): # Add a note after the end of the song.  Pad the extra space with zeros.
        song = np.concat( (song,  np.zeros(sample_idx  - len(song)), note ))
        return song
    elif sample_idx + len(note) > len(song): # Add a note overlapping the end of the song
        len_result = sample_idx + len(note)
        padded_note = np.concat( (np.zeros(sample_idx), note) )
        padded_song = np.concat( (song, np.zeros(len_result - len(song))) )
        return padded_song + padded_note
    else:   # Add a note that ends before the end of the song
        start_of_note = sample_idx
        end_of_note = sample_idx + len(note)
        padded_note = np.concat( (np.zeros(start_of_note), note, np.zeros(len(song) - end_of_note)))
        return padded_note + song

def make_song_from_array(note, song_array, samples_between_notes, zero_note):
    #song_array = [[0, 12, 400, 400, 7, 7]] # rest for undefined notes
    notes = {}
    sound_signal = note[0:0]
    for score in song_array:
        sample_idx = 0
        for note_idx in range(len(score)):
            this_note_obj = score[note_idx]

            if isinstance(this_note_obj, int):  # simple note
                note_value = this_note_obj + zero_note
                if note_value not in notes:
                    notes[note_value] = librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=bins_per_octave, n_steps=note_value, scale=True)
                sound_signal = add_new_note(sound_signal, notes[note_value], sample_idx)
                sample_idx = sample_idx + int(samples_between_notes)
            elif isinstance(this_note_obj, list) and isinstance(this_note_obj[0], int):   #note that may be of a different length than a simple note
                note_value = this_note_obj[0] + zero_note
                if note_value not in notes:
                    notes[note_value] = librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=bins_per_octave, n_steps=note_value, scale=True)
                sound_signal = add_new_note(sound_signal, notes[note_value], sample_idx)
                sample_idx = sample_idx + int(samples_between_notes * this_note_obj[1])
            elif isinstance(this_note_obj, list) and isinstance(this_note_obj[0], str): #rests 
                sound_signal = add_new_note(sound_signal, 0*notes[0], sample_idx)
                sample_idx = sample_idx + int(samples_between_notes * this_note_obj[1])
            elif isinstance(this_note_obj, list) and isinstance(this_note_obj[0], tuple):
                note_values = [n[0] + zero_note for n in this_note_obj]
                note_time_values = [t[1] for t in this_note_obj]
                delay_values = [d[2] for d in this_note_obj]
                max_note_length = int(max([note_time_values[i] + delay_values[i] for i in range(len(note_time_values))]) * samples_between_notes)
                for ix in range(len(note_values)):
                    note_value = note_values[ix]
                    if note_value not in notes:
                        notes[note_value] = librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=bins_per_octave, n_steps=note_value, scale=True)
                    delay = int(delay_values[ix] * samples_between_notes)
                    sound_signal = add_new_note(sound_signal, notes[note_value], sample_idx + delay)
                sample_idx = sample_idx + max_note_length
                
            # if isinstance(this_note_obj, int):  # simple note
            #     sample_idx = sample_idx + int(samples_between_notes)
            # elif isinstance(this_note_obj, list):   #note that may be of a different length than a simple note
            #     sample_idx = sample_idx + int(samples_between_notes * this_note_obj[1])
    return sound_signal

input_sound_file = 'sound_test/66218__percussionfiend__2.wav'
output_sound_file = 'sound_test/output.wav'

bins_per_octave = 12
note_trim_fraction = 1.0    # can trim off end of note if desired (just make this less than 1.0)
time_between_notes = 0.25  # you can choose the shortest note (e.g. an eighth note) to avoid fractions in the song array,
                            # though it's not required
zero_note = -10

mode = 'abc'

if mode == 'native':
    song_array_str = '''[
    [[(0,1,0),(4,1,0),(7,1,0)], [5,2], 5, 7, 9, 5,  #Tis a gift to be simple,
     9, 10, [12,2], 12, 10, [9,2],  # Tis a gift to be free.
     7, 5, [7,2], [7,2], [7,2], [5,2], 7, 9, 7, 4, [0,2], # Tis a gift to come down where we ought to be,
     [0,2], 5, 4, 5, 7, [9,2], 7, 7, [9,2], [10,2], [12,2], # and when we find ourselves in the place just right,
     [9,2], [7,2], 7, 7, 9, [9,2], 7, [5,2], 5, 5, [5,4], # t'will be in the valley of love and delight.
     [12,4], [9,3], 7, 9, 10, 9, 7, [5,3], # When true simplicity is gained,
     7, [9,2], 9, 10, [12,2], [9,2], [7,2], 7, 9, [7,2], #to bow and to bend we shan't be ashamed.
     [0,2], [5,4], [5,3], 7, [9,2], 9, 10, [12,2], # To turn, turn, will be our delight,
     10, 9, [7,2], [7,2], [9,2], 9, 7, [5,2], [5,2], [5,4]], # till by turning, turning we come out right.
     []
     ]'''
    song_array = eval(song_array_str)
elif mode == 'abc':
    this_abc_song = '''
X:1
%
T:Face Me Up
M:C|
L:1/8
R:Hornpipe
S:Kerr - Merry Melodies, vol. 4, No. 306
Z:AK/Fiddler's Companion
K:F
c2f2d2f2 | (cd)cB AG F2 | ABcd efga |1 (g^f)ga g4 :|2 (gf)ga f4 ||
|: bagb agfa | gfeg f2a2 | g^fga g=fed | (c=B)cd (c_B)AB |
c2f2d2f2 | (cd)cB AB c2 | defd efge | f2a2f2z5 :||
'''
    song_array = abc_to_song_array(this_abc_song)


note, sample_rate = librosa.load(input_sound_file)

if note_trim_fraction > 1.0:
    note_trim_fraction = 1.0
note = note[0: int(note_trim_fraction * len(note))] #trim off quiet following the note


samples_between_notes = time_between_notes * sample_rate

# song_array = [[0, 2, 4, 5, 7, 9, 11, 12], [2, 4, 5, 7, 9, 11, 12, 14], [4, 5, 7, 9, 11, 12, 14, 16]]  # do re mi, plus friends

# Notes and note groups can take three forms:
# Integer N : Note that will have pitch / note number P and duration time_between_notes.
# list of two ints [N, T]: Note that will have pitch / note number A and last T*time_between_notes
# list of tuples [(N1,T1,D1), (N2,T2,D2), (N3,T3,D3)...]: Multiple notes, each with pitch/note number N,
#   duration T*time_between_notes, and delay D before the beginning of the note.
#   The note group will be assumed to last max(Ti + Di) for all i.
#   This allows the entry of multiple notes at the same time, as well as delays.

sound_signal = make_song_from_array(note=note, song_array=song_array, samples_between_notes=samples_between_notes, zero_note=zero_note)

soundfile.write(output_sound_file, sound_signal, sample_rate)
print('Done! ' + str(datetime.now()))
x = 2
