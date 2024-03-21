MAX_LENGTH_NOTE_ARRAY = 15
THREADS_PER_BLOCK = [8, 8]
FRACTAL_CHANNEL = 8
CAMERA_INDEX = 0
STEPS = 3

# resolucion
WIDTH = 720 #1920
HEIGHT = 480 #1080

PATH_TO_BASS_FOLDER = 'midis/bass'
PATH_TO_DRUM_FOLDER = 'midis/drums'
PATH_TO_MELODY_FOLDER = 'midis/melody'
PATH_TO_CHORDS_FOLDER = 'midis/chords'
PATH_TO_MELODY_NEW_CHANNEL_FOLDER = 'midis/melody_new_channel'
PATH_TO_PRETRAINED_ATTENTION_RNN = 'pretrained_models/attention_rnn.mag'
PATH_TO_PRETRAINED_BASIC_RNN = 'pretrained_models/basic_rnn.mag'
PATH_TO_PRETRAINED_DRUM_KIT_RNN = 'pretrained_models/drum_kit_rnn.mag'
PATH_TO_PRETRAINED_GROOVE_VAE = 'pretrained_models/groovae_4bar.tar'
PATH_TO_PRETRAINED_POLYPHONY_RNN = 'pretrained_models/polyphony_rnn.mag'
PATH_TO_PRETRAINED_PIANO_ROLL = 'pretrained_models/pianoroll_rnn_nade.mag'
PATH_TO_PRETRAINED_CHORD_PITCHES_IMPROV = 'pretrained_models/chord_pitches_improv.mag'
PATH_TO_FINAL_MIDI = 'midis/final_midis'
PATH_TO_MIDIS_FOR_STRUCTURE = 'midis/structure'
PATH_TO_MIDIS_PROCESSED = 'midis/structure_processed'

MIDI_STRUCTURE = ['A', 'B', 'A', 'B', 'C', 'B']
MIDI_TRACKS = [1, 1, 1]
BASS_CHANNEL = 2    # Reaper +1. No se usan en configuracion, esto es info nada mas.
DRUMS_CHANNEL = 9   # Default percusion
MELODY_CHANNEL = 3
CHORDS_CHANNEL = 4
FRACTAL_CHANNEL = 8

INSTRUMENTS = ['bass', 'drum', 'melody', 'chords']
BASS_TEMPERATURE = 0.5
DRUM_TEMPERATURE = 0.1
MIDI_NUM_STEPS = 64
BASS_PRIMER_MELODY = "[24]"
MELODY_PRIMER_MELODY = "[60]"
MELODY_PRIMER_PITCHES = "[72,76,79]"
BACKING_CHORDS = "Cmaj7 G6 Am7 Fmaj7"

VELOCITY = 'velocity'
TEMPO = 'tempo'
PITCH = 'pitch'
VOLUME = 'volume'
IS_MINOR = 'is_minor'
MIDI = 'midi'
EMOTION = 'emotion'
CHANGE_DETECTED = 'change_detected'
COLOR_ITER = 'color_iter'

SAD_SONG = -50   # from -127 to -50
HAPPY_SONG = 70  # from 70 to 127

LOGGING_LEVEL = "INFO"     # OPTIONS: INFO, DEBUG, ERROR, WARNING

#GRADIENT_IMAGE_PATH = "source/imgs/fuego dallee.webp"
GRADIENT_IMAGE_PATH = "source/imgs/psicodelic.PNG"