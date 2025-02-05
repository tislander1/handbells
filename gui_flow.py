import os
import sys
import json
import time
import webbrowser
from PySide6.QtGui import QTextCursor, QFont, QAction
from PySide6.QtWidgets import QPushButton, QLineEdit, QLabel, QComboBox, QPlainTextEdit, QCheckBox
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QMainWindow, QGroupBox

import librosa
import soundfile
import traceback
import sounddevice
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

def make_song_from_array(note, song_array, samples_between_notes, zero_note, sample_rate, bins_per_octave, invert):
    #song_array = [[0, 12, 400, 400, 7, 7]] # rest for undefined notes
    notes = {}
    sound_signal = note[0:0]
    for score in song_array:
        sample_idx = 0
        for note_idx in range(len(score)):
            this_note_obj = score[note_idx]

            if isinstance(this_note_obj, int):  # simple note
                note_value = this_note_obj*invert + zero_note
                if note_value not in notes:
                    notes[note_value] = librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=bins_per_octave, n_steps=note_value, scale=True)
                sound_signal = add_new_note(sound_signal, notes[note_value], sample_idx)
                sample_idx = sample_idx + int(samples_between_notes)
            elif isinstance(this_note_obj, list) and isinstance(this_note_obj[0], int):   #note that may be of a different length than a simple note
                note_value = this_note_obj[0]*invert + zero_note
                if note_value not in notes:
                    notes[note_value] = librosa.effects.pitch_shift(y=note, sr=sample_rate, bins_per_octave=bins_per_octave, n_steps=note_value, scale=True)
                sound_signal = add_new_note(sound_signal, notes[note_value], sample_idx)
                sample_idx = sample_idx + int(samples_between_notes * this_note_obj[1])
            elif isinstance(this_note_obj, list) and isinstance(this_note_obj[0], str): #rests 
                sound_signal = add_new_note(sound_signal, 0*notes[0], sample_idx)
                sample_idx = sample_idx + int(samples_between_notes * this_note_obj[1])
            elif isinstance(this_note_obj, list) and isinstance(this_note_obj[0], tuple):
                note_values = [n[0]*invert + zero_note for n in this_note_obj]
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


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("XyloFonyX Music Studio ver. 0.1")
        self.setStyleSheet("color: black; selection-color: blue; background-color: rgba(200, 200, 255, 255);") 

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        helpMenu = menuBar.addMenu('&Help')

        openAction = QAction('&Load', self)
        saveAction = QAction('&Save', self)
        helpAction = QAction('&Help manual', self)    
        helpAction.triggered.connect(self.open_help_menu)
 

        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        helpMenu.addAction(helpAction)

        


        self.tok = {}
        self.program_config = {
             'data': {'note': '', 'mode': '', 'half_steps_per_octave': '', 
             'trim': '', 'zero_note': '', 'song': '', 'time_between_notes': '', 'invert_melody': ''}
             }

        print('Loading window.')

        self.layout1 = QVBoxLayout() #main layout for window
        self.layout1.setContentsMargins(0,0,0,0)
        self.layout1.setSpacing(10)
        
        #finder tool    -------------------------------------------------------------------
        layout_finder = QHBoxLayout() 
        note_sample_text = QLabel(" Note sample (.wav or .mp3): ")
        layout_finder.addWidget(note_sample_text)
        self.tok['note'] = QLineEdit('sound_test/66218__percussionfiend__2.wav')
        self.tok['note'].setStyleSheet("background-color:rgba(200,230,200,255)")
        text1 = QLabel(" Mode: ")
        self.tok['mode'] = QComboBox()
        self.tok['mode'].setStyleSheet("background-color:rgba(200,230,200,255)")
        self.tok['mode'].addItems(['ABC notation', 'XyloFonyX'])
        layout_finder.addWidget(self.tok['note'])
        layout_finder.addWidget(text1)
        layout_finder.addWidget(self.tok['mode'])
        groupbox1 = QGroupBox("Instrument and mode selection")
        groupbox1.setLayout(layout_finder)
        self.layout1.addWidget(groupbox1)

        #Config -----------------------------------------------------------------------------------
        layout_config_row1 = QHBoxLayout() # config options
        layout_config_row2 = QHBoxLayout()
        layout_all_config = QVBoxLayout()

        text_pub1 = QLabel(" Half steps per octave (default 12):")
        self.tok['half_steps_per_octave'] = QLineEdit("12")
        self.tok['half_steps_per_octave'].setStyleSheet("background-color:rgba(200,230,200,255)")
        text_trim = QLabel(" Note trim (0 to 1):")
        self.tok['trim'] = QLineEdit("1.0")
        self.tok['trim'].setStyleSheet("background-color:rgba(200,230,200,255)")
        frequency_shift_number = QLabel(" Frequency shift (half steps):")
        self.tok['zero_note'] = QLineEdit("-10")
        self.tok['zero_note'].setStyleSheet("background-color:rgba(200,230,200,255)")  
        time_btw_notes_label = QLabel(" Time between notes (sec):")
        self.tok['time_between_notes'] = QLineEdit("0.25")
        self.tok['time_between_notes'].setStyleSheet("background-color:rgba(200,230,200,255)")  
        self.tok['invert_melody'] = QCheckBox('Invert melody')

        layout_config_row1.addWidget(text_pub1)
        layout_config_row1.addWidget(self.tok['half_steps_per_octave'])
        layout_config_row1.addWidget(text_trim)
        layout_config_row1.addWidget(self.tok['trim'])

        layout_config_row2.addWidget(frequency_shift_number)
        layout_config_row2.addWidget(self.tok['zero_note'])
        layout_config_row2.addWidget(time_btw_notes_label)
        layout_config_row2.addWidget(self.tok['time_between_notes'])     
        layout_config_row2.addWidget(self.tok['invert_melody']) 

        layout_all_config.addLayout(layout_config_row1)   
        layout_all_config.addLayout(layout_config_row2)

        groupbox_pub = QGroupBox("Configuration")
        groupbox_pub.setLayout(layout_all_config)
        self.layout1.addWidget(groupbox_pub)

        layout_main_song_section = QVBoxLayout() #main layout for window

        #Main recipe --------------------------------------------------------------------------

        layout_song = QVBoxLayout()
        self.tok['song'] = QPlainTextEdit('')
        self.tok['song'].setStyleSheet("background-color:rgba(200,200,200,255)")  
        layout_song.addWidget(self.tok['song'])
        
        song_generator_button = QPushButton("Press here to generate a song!")
        song_generator_button.setStyleSheet("background-color:rgba(160,255,160,255)")
        song_generator_button.setFont(QFont('Arial', 15)) 
        song_generator_button.clicked.connect(self.generate_song)
        layout_song.addWidget(song_generator_button)

        layout_main_song_section.addLayout(layout_song)

        groupbox_main_recipe = QGroupBox("Enter a song in abc notation or xylofonyx format (set the mode appropriately!)")
        groupbox_main_recipe.setLayout(layout_main_song_section)
        self.layout1.addWidget(groupbox_main_recipe)

        #Save and load the recipe --------------------------------------------------------------------------
        layout_saver = QHBoxLayout() # saver tool
        text_dB_file = QLabel(" File:")
        self.tok['json_file'] = QLineEdit("my song file.json")
        self.tok['json_file'].setStyleSheet("background-color:rgba(200,230,200,255)")
        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color:rgba(200,230,200,255)")  
        save_button.clicked.connect(self.save_button_handler)
        spacer = QLabel('      ')
        load_button = QPushButton("Load")
        load_button.setStyleSheet("background-color:rgba(200,230,200,255)")  
        load_button.clicked.connect(self.load_button_handler)
        layout_saver.addWidget(text_dB_file)
        layout_saver.addWidget(self.tok['json_file'])
        layout_saver.addWidget(save_button)
        layout_saver.addWidget(load_button)
        self.layout1.addLayout( layout_saver )

        status_panel = QHBoxLayout()
        self.tok['status'] = QPlainTextEdit('')
        self.tok['status'].setReadOnly(True)
        self.tok['status'].setMaximumSize(10000, 100)
        status_panel.addWidget(self.tok['status'])
        status_groupbox = QGroupBox("Program status")
        status_groupbox.setMaximumHeight(120)
        status_groupbox.setLayout(status_panel)
        self.layout1.addWidget(status_groupbox)

        widget = QWidget()
        widget.setLayout(self.layout1)
        self.setCentralWidget(widget)

        self.program_config['data']['note'] = self.tok['note'].text()
        self.program_config['data']['mode'] = self.tok['mode'].currentText()
        self.program_config['data']['half_steps_per_octave'] = self.tok['half_steps_per_octave'].text()
        self.program_config['data']['trim'] = self.tok['trim'].text() 
        self.program_config['data']['zero_note'] = self.tok['zero_note'].text()
        self.program_config['data']['time_between_notes'] = self.tok['time_between_notes'].text()          
        self.program_config['data']['song'] = self.tok['song'].toPlainText()
    
    def open_help_menu(self):
        webbrowser.open('file://' + os.path.realpath('help.html'))

    def generate_song(self):
        try:

            self.tok['status'].insertPlainText('\nBeginning song generation.')
            self.tok['status'].moveCursor(QTextCursor.End)

            input_sound_file = self.tok['note'].text()
            mode = self.tok['mode'].currentText()
            bins_per_octave = int(self.tok['half_steps_per_octave'].text())
            note_trim_fraction = float(self.tok['trim'].text())    # can trim off end of note if desired (just make this less than 1.0)
            zero_note = float(self.tok['zero_note'].text())
            time_between_notes = float(self.tok['time_between_notes'].text())  # you can choose the shortest note (e.g. an eighth note)
                                                    # to avoid fractions in the song array, though it's not required

            invert_melody_checked = self.tok['invert_melody'].isChecked()
            song_array_str = self.tok['song'].toPlainText()

            output_sound_file = 'output.wav'

            invert_melody_multiplier = -1 if invert_melody_checked else 1

            if mode == 'XyloFonyX':
                song_array = eval(song_array_str)
            elif mode == 'ABC notation':
                song_array = abc_to_song_array(song_array_str)

            note, sample_rate = librosa.load(input_sound_file)

            if note_trim_fraction > 1.0:
                note_trim_fraction = 1.0
            note = note[0: int(note_trim_fraction * len(note))] #trim off quiet following the note

            samples_between_notes = time_between_notes * sample_rate

            sound_signal = make_song_from_array(note=note, song_array=song_array,
                                                samples_between_notes=samples_between_notes, zero_note=zero_note,
                                                sample_rate=sample_rate, bins_per_octave=bins_per_octave,
                                                invert=invert_melody_multiplier)

            soundfile.write(output_sound_file, sound_signal, sample_rate)
            self.tok['status'].insertPlainText('\nResults written to ' + output_sound_file + '.')
            self.tok['status'].insertPlainText('\nDone! Current time is ' + str(datetime.now()) + '.')
            self.tok['status'].moveCursor(QTextCursor.End)
            sounddevice.play(sound_signal, sample_rate)
        except Exception:
            self.tok['status'].insertPlainText('\nException:')
            self.tok['status'].insertPlainText('\n' + traceback.format_exc())


    def update_program_record(self):
        self.program_config['data']['note'] = self.tok['note'].text()
        self.program_config['data']['mode'] = self.tok['mode'].currentText()
        self.program_config['data']['half_steps_per_octave'] = self.tok['half_steps_per_octave'].text()
        self.program_config['data']['trim'] = self.tok['trim'].text() 
        self.program_config['data']['zero_note'] = self.tok['zero_note'].text()
        self.program_config['data']['time_between_notes'] = self.tok['time_between_notes'].text()          
        self.program_config['data']['song'] = self.tok['song'].toPlainText()
        self.program_config['data']['invert_melody'] = self.tok['invert_melody'].isChecked()

    def update_program_display(self):
        self.tok['note'].setText(self.program_config['data']['note'])
        self.tok['mode'].setCurrentText(self.program_config['data']['mode'])
        self.tok['half_steps_per_octave'].setText(self.program_config['data']['half_steps_per_octave'])
        self.tok['trim'].setText(self.program_config['data']['trim'])
        self.tok['zero_note'].setText(self.program_config['data']['zero_note'])
        self.tok['time_between_notes'].setText(self.program_config['data']['time_between_notes'])
        self.tok['song'].setPlainText(self.program_config['data']['song'])
        self.tok['invert_melody'].setChecked(self.program_config['data']['invert_melody'])


    def save_button_handler(self):
        print('Save button clicked.')
        self.tok['status'].moveCursor(QTextCursor.End)
        self.update_program_record()
        file_name = self.tok['json_file'].text()
        with open(file_name, 'w') as f:
            json.dump(self.program_config, f)
        self.tok['status'].insertPlainText('Program data saved to ' + str(file_name) +'\n')
            
    def load_button_handler(self):
        print('Load button clicked.')
        self.tok['status'].moveCursor(QTextCursor.End)
        file_name = self.tok['json_file'].text()
        with open(file_name, 'r') as f:
            self.program_config = json.load(f)
        autobackup_file = file_name + '_' + time.strftime("%Y%m%d_%H%M%S") +'.json'
        with open(autobackup_file, 'w') as f:
            json.dump(self.program_config, f)
        self.tok['status'].insertPlainText('Program data read from ' + str(file_name) + '\n')
        self.update_program_display()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()