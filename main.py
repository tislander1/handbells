import librosa
import soundfile
import numpy as np

def add_new_note(song, note, sample_idx):
    if sample_idx + len(note) > len(song):
        len_result = sample_idx + len(note)
        padded_note = np.concat( (np.zeros(sample_idx), note) )
        padded_song = np.concat( (song, np.zeros(len_result - len(song))) )
        return padded_song + padded_note
    else:
        start_of_note = sample_idx
        end_of_note = sample_idx + len(note)
        padded_note = np.concat( (np.zeros(start_of_note), note, np.zeros(len(song) - end_of_note)))
        return padded_note + song

note, sample_rate = librosa.load('sound_test/11079__angstrom__d1.wav')
note = note[0:len(note)//3] #trim off quiet following the note
num_notes_lower = 37
num_notes_higher = 13
first_note = 0
last_note = num_notes_lower + num_notes_higher - 1

time_between_notes = 0.25
zero_note = 30

samples_between_notes = time_between_notes * sample_rate

notes = {}
for note_int in range(-1*num_notes_lower, num_notes_higher):
    scaled_note= librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=12, n_steps=note_int, scale=True)
    notes[note_int + num_notes_lower] = scaled_note

# song_array = [[0, 2, 4, 5, 7, 9, 11, 12], [2, 4, 5, 7, 9, 11, 12, 14], [4, 5, 7, 9, 11, 12, 14, 16]]  # do re mi, plus friends
song_array = [[0, 0, 5, 5, 7, 9, 5, 400,  #Tis a gift to be simple
               9, 10, 12, 12, 10, 9, 400, # Tis a gift to be free
               7, 5, 7, 7, 7, 5, 7, 9, 7, 4, 0, 400, # tis a gift to come down where we ought to be
               0, 5, 4, 5, 7, 9, 7, 7, 9, 10, 12, 400, # and when we find ourselves in the place just right
               9, 7, 7, 7, 9, 9, 7, 5, 5, 5, 5, 400, 400, # t'will be in the valley of love and delight
               12, 9, 7, 9, 10, 9, 7, 5, 400, # when true simplicity is gained
               7, 9, 9, 10, 12, 9, 7, 7, 9, 7, 400, #to bow and to bend we shan't be ashamed
               0, 5, 5, 7, 9, 9, 10, 12, 400, # to turn, turn, will be our delight
               10, 9, 7, 7, 9, 9, 7, 5, 5, 5] # till by turning, turning we come out right
               ]
#song_array = [[0, 12, 400, 400, 7, 7]] # rest for undefined notes
sound_signal = notes[0][0:1]
for score in song_array:
    for note_idx in range(len(score)):
        note_value = score[note_idx] + zero_note
        sample_idx = int(samples_between_notes * note_idx)
        if note_value in notes:
            sound_signal = add_new_note(sound_signal, notes[note_value], sample_idx)
        else:
            sound_signal = add_new_note(sound_signal, 0*notes[0], sample_idx) # rest if there is no note defined
        x = 2
soundfile.write('sound_test/output_song.wav', sound_signal, sample_rate)
x = 2
