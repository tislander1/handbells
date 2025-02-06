import random
import math

harmonic_ratios = [round(1000*math.log((x))/math.log(2)) for x in [1,1.2,1.25,1.333,1.5, 1.6, 1.667,2]]

my_note_list = [0]
for ix in range(2000):
    previous_note = my_note_list[-1]
    note_adjustment = random.choice(harmonic_ratios)
    note_increase = random.choice([-1, 1])
    note_adjustment = note_adjustment * note_increase
    new_note = previous_note + note_adjustment
    if abs(new_note) > 2600:
        new_note = 0
    my_note_list.append(new_note)

print(my_note_list)