import librosa
import soundfile

song, sample_rate = librosa.load('sound_test/11079__angstrom__d1.wav')
song = song[0:len(song)//3]
for note_int in range(-37, 1):
    scaled_song = librosa.effects.pitch_shift(y=song, sr=sample_rate, bins_per_octave=12, n_steps=note_int, scale=True)
    soundfile.write('sound_test/scaled_song'+ str(note_int) +'.wav', scaled_song, sample_rate)
