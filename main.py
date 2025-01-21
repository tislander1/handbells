import librosa
import soundfile

song, sample_rate = librosa.load('sound_test/11079__angstrom__d1.wav')
song = song[0:len(song)//3]
soundfile.write('sound_test/stereo_file.wav', song, sample_rate)
