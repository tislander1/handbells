import os
import sys
import json
import time
import webbrowser
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPushButton, QLineEdit, QLabel, QComboBox, QPlainTextEdit
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QMainWindow, QGroupBox


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("XyloFonyX Music Studio ver. 0.1")

        self.tok = {}
        self.program_config = {
             'data': [{'note': '', 'mode': '', 'half_steps_per_octave': '', 'trim': '', 'zero_note': '', 'song': ''}]
             }
        self.program_pointer = 0
        self.previous_program_pointer = 0

        print('Loading window.')

        self.layout1 = QVBoxLayout() #main layout for window
        self.layout1.setContentsMargins(0,0,0,0)
        self.layout1.setSpacing(10)
        
        #finder tool    -------------------------------------------------------------------
        layout_finder = QHBoxLayout() 
        note_sample_text = QLabel(" Note sample (.wav or .mp3): ")
        layout_finder.addWidget(note_sample_text)
        self.tok['note'] = QLineEdit('sound_test/66218__percussionfiend__2.wav')
        text1 = QLabel(" Mode: ")
        self.tok['mode'] = QComboBox()
        self.tok['mode'].addItems(['ABC notation', 'XyloFonyX'])
        layout_finder.addWidget(self.tok['note'])
        layout_finder.addWidget(text1)
        layout_finder.addWidget(self.tok['mode'])
        groupbox1 = QGroupBox("Recipe Finder")
        groupbox1.setLayout(layout_finder)
        self.layout1.addWidget(groupbox1)

        #Publishing -----------------------------------------------------------------------------------
        layout_pub = QHBoxLayout() # publishing tool

        text_pub1 = QLabel(" Half steps per octave (default 12):")
        self.tok['half_steps_per_octave'] = QLineEdit("12")

        text_trim = QLabel(" Note trim (0 to 1):")
        self.tok['trim'] = QLineEdit("1.0")

        frequency_shift_number = QLabel(" Frequency shift (half steps):")
        self.tok['zero_note'] = QLineEdit("-10")  

        time_btw_notes_label = QLabel(" Time between notes (sec):")
        self.tok['time_between_notes'] = QLineEdit("0.25")

        layout_pub.addWidget(text_pub1)
        layout_pub.addWidget(self.tok['half_steps_per_octave'])

        layout_pub.addWidget(text_trim)
        layout_pub.addWidget(self.tok['trim'])

        layout_pub.addWidget(time_btw_notes_label)
        layout_pub.addWidget(self.tok['time_between_notes'])        
        
        layout_pub.addWidget(frequency_shift_number)
        layout_pub.addWidget(self.tok['zero_note'])

        groupbox_pub = QGroupBox("Configuration")
        groupbox_pub.setLayout(layout_pub)
        self.layout1.addWidget(groupbox_pub)

        layout_main_song_section = QVBoxLayout() #main layout for window

        #Main recipe --------------------------------------------------------------------------

        layout_song = QVBoxLayout()
        self.tok['song'] = QPlainTextEdit('')
        layout_song.addWidget(self.tok['song'])
        
        song_generator_button = QPushButton("Generate a song!")
        song_generator_button.clicked.connect(self.generate_song)
        layout_song.addWidget(song_generator_button)

        layout_main_song_section.addLayout(layout_song)


        groupbox_main_recipe = QGroupBox("Enter a song in ABC notation or Xylofonyx format")
        groupbox_main_recipe.setLayout(layout_main_song_section)
        self.layout1.addWidget(groupbox_main_recipe)

        #Save and load the recipe --------------------------------------------------------------------------
        layout_saver = QHBoxLayout() # saver tool
        text_dB_file = QLabel(" File:")
        self.tok['json_file'] = QLineEdit("my song file.json")
        save_button = QPushButton("Save Recipes")
        save_button.clicked.connect(self.save_button_handler)
        spacer = QLabel('      ')
        load_button = QPushButton("Load Recipes")
        load_button.clicked.connect(self.load_button_handler)
        layout_saver.addWidget(text_dB_file)
        layout_saver.addWidget(self.tok['json_file'])
        layout_saver.addWidget(save_button)
        layout_saver.addWidget(spacer)
        layout_saver.addWidget(load_button)
        layout_saver.addWidget(spacer)
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

    def generate_song(self):
        pass

    def update_program_record(self):
        self.program_config['data']['note'] = self.tok['note'].text()
        self.program_config['data']['mode'] = self.tok['mode'].text()
        self.program_config['data']['half_steps_per_octave'] = self.tok['half_steps_per_octave'].text()
        self.program_config['data']['trim'] = self.tok['trim'].text() 
        self.program_config['data']['zero_note'] = self.tok['zero_note'].text()           
        self.program_config['data']['song'] = self.tok['song'].toPlainText()

    def update_program_display(self):
        self.tok['note'].setText(self.program_config['data']['note'])
        self.tok['mode'].setText(self.program_config['data']['mode'])
        self.tok['half_steps_per_octave'].setText(self.program_config['data']['half_steps_per_octave'])
        self.tok['trim'].setText(self.program_config['data']['trim'])
        self.tok['zero_note'].setText(self.program_config['data']['zero_note'])
        self.tok['song'].setPlainText(self.program_config['data']['song'])

    def save_button_handler(self):
        print('Save button clicked.')
        self.tok['status'].moveCursor(QTextCursor.End)
        file_name = self.tok['json_file'].text()
        with open(file_name, 'w') as f:
            json.dump(self.program_config, f)
        self.tok['status'].insertPlainText('Recipes saved to ' + str(file_name) +'\n')
            
    def load_button_handler(self):
        print('Load button clicked.')
        self.tok['status'].moveCursor(QTextCursor.End)
        file_name = self.tok['json_file'].text()
        with open(file_name, 'r') as f:
            self.program_config = json.load(f)
        autobackup_file = file_name + '_' + time.strftime("%Y%m%d_%H%M%S") +'.json'
        with open(autobackup_file, 'w') as f:
            json.dump(self.program_config, f)
        self.tok['status'].insertPlainText('Recipes read from ' + str(file_name) + '\n')
        self.previous_program_pointer = len(self.program_config['data']) - 1
        self.program_pointer = self.previous_program_pointer
        self.update_program_display(self.program_pointer)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()