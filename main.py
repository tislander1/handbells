import librosa
import soundfile
import numpy as np

def add_new_note_to_end_of_song(song, note, sample_idx):
    len_result = sample_idx + len(note)
    padded_note = np.concat( (np.zeros(sample_idx), note) )
    padded_song = np.concat( (song, np.zeros(len_result - len(song))) )
    return padded_song + padded_note

note, sample_rate = librosa.load('sound_test/11079__angstrom__d1.wav')
note = note[0:len(note)//3] #trim off quiet following the note
num_notes_lower = 37
num_notes_higher = 13
first_note = 0
last_note = num_notes_lower + num_notes_higher - 1

time_between_notes = 0.5
zero_note = 30

samples_between_notes = time_between_notes * sample_rate

notes = {}
for note_int in range(-1*num_notes_lower, num_notes_higher):
    scaled_note= librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=12, n_steps=note_int, scale=True)
    notes[note_int + num_notes_lower] = scaled_note

song_array = [[0, 2, 4, 5, 7, 9, 11, 12], []]  # do re mi, plus an empty song

sound_signal = notes[0][0:1]
for score in song_array:
    for note_idx in range(len(score)):
        note_value = score[note_idx] + zero_note
        sample_idx = int(samples_between_notes * note_idx)
        sound_signal = add_new_note_to_end_of_song(sound_signal, notes[note_value], sample_idx)
        x = 2
soundfile.write('sound_test/output_song.wav', sound_signal, sample_rate)
x = 2
