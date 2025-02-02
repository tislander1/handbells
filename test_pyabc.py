from pyabc import Tune

# with open('sound_test/oaken-leaves-abc.txt', 'r') as f:
with open('sound_test/valce-ardennaise.abc', 'r') as f:
    abc_lines = f.readlines()
    this_abc_song = ''.join(abc_lines)

tune1 = Tune(abc=this_abc_song)
print(tune1.tokens)
pitches = [item.pitch.abs_value for item in tune1.tokens if hasattr(item, 'pitch') ] 
print('pitches:', pitches)
x = 2