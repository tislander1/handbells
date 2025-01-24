from mido import MidiFile

midi_song = MidiFile('sound_test/Fur Elise.mid', clip=True)

division_val = 50
song_list = []
for trk_idx in range(len(midi_song.tracks)):
    song_list.append([])
    for msg in midi_song.tracks[trk_idx]:
        if msg.type == 'note_on':
            song_list[-1].append([msg.note, msg.time/division_val])
x = 2
