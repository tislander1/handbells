import librosa
import soundfile

song, sample_rate = librosa.load('sound_test/11079__angstrom__d1.wav')
song = song[0:len(song)//3]
num_notes_lower = 37
num_notes_higher = 13
for note_int in range(-1*num_notes_lower, num_notes_higher):
    scaled_song = librosa.effects.pitch_shift(y=song, sr=sample_rate, bins_per_octave=12, n_steps=note_int, scale=True)
    soundfile.write('sound_test/note_num'+ str(num_notes_lower+note_int) +'.wav', scaled_song, sample_rate)
