import mido

import classes.config as config
from classes.logger.logger import Logger

import os
import datetime
import pretty_midi


class Generator:
    """
    Esta clase genera todos los midis necesarios para como minimo generar un tema con una estructura.
    Podemos decir que genera la cancion
    """
    def __init__(self, midi_structure=config.MIDI_STRUCTURE, backing_chords=config.BACKING_CHORDS,
                 melody_primer_melody=config.MELODY_PRIMER_MELODY, bass_primer_melody=config.BASS_PRIMER_MELODY):
        self.log = Logger("Generator", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.open_ports = []

        self.midi_final = config.PATH_TO_FINAL_MIDI
        self.drum_path = config.PATH_TO_DRUM_FOLDER
        self.bass_path = config.PATH_TO_BASS_FOLDER
        self.melody_path = config.PATH_TO_MELODY_FOLDER
        self.chords_path = config.PATH_TO_CHORDS_FOLDER
        self.bass_bundle = config.PATH_TO_PRETRAINED_BASIC_RNN
        self.drum_checkpoint = config.PATH_TO_PRETRAINED_GROOVE_VAE
        self.chords_bundle = config.PATH_TO_PRETRAINED_CHORD_PITCHES_IMPROV
        self.path_to_midis_for_structure = config.PATH_TO_MIDIS_FOR_STRUCTURE

        self.bass_channel = config.BASS_CHANNEL
        self.drums_channel = config.DRUMS_CHANNEL
        self.chords_channel = config.CHORDS_CHANNEL
        self.melody_channel = config.MELODY_CHANNEL

        self.bass_temperature = config.BASS_TEMPERATURE
        self.drum_temperature = config.DRUM_TEMPERATURE
        self.instruments = config.INSTRUMENTS
        self.backing_chords = backing_chords
        self.bass_primer_melody = bass_primer_melody
        self.melody_primer_melody = melody_primer_melody

        self.num_steps = str(config.MIDI_NUM_STEPS)
        self.midi_structure = midi_structure
        self.num_song_parts = len(self.midi_structure)
        self.num_outputs = len(set(self.midi_structure))

    def modify_channel(self, msg, channel_value):
        """
        Modifies the channel of the MIDI message.
        Channel values must be integers between 0 and 15.

        :param msg: MIDI message.
        :param channel_value: Desired channel value (0-15).
        :return: Modified MIDI message.
        """
        if hasattr(msg, 'channel'):
            msg.channel = channel_value
        return msg

    def change_channels_of_one_file(self, midi_file, new_channel):

        modified_midi = mido.MidiFile(ticks_per_beat=midi_file.ticks_per_beat)

        for track in midi_file.tracks:
            modified_track = mido.MidiTrack()

            for msg in track:
                modified_msg = self.modify_channel(msg.copy(), new_channel)
                modified_track.append(modified_msg)

            modified_midi.tracks.append(modified_track)

        return modified_midi

    def change_channels_of_tracks(self, path_to_midi_final, channel_assignments):
        midi_file = mido.MidiFile(path_to_midi_final)

        modified_midi = mido.MidiFile(ticks_per_beat=midi_file.ticks_per_beat)
        self.log.debug(f'change_channels_of_tracks: tracks = {len(midi_file.tracks)}')

        for track_number, track in enumerate(midi_file.tracks):
            try:
                new_channel = channel_assignments[track_number]
                self.log.debug(f'change_channels_of_tracks: track_number {track_number}, new_channel {new_channel}')
            except:
                new_channel = 14
                self.log.warning(
                    f'No channel assignment for track {track_number}. Using fallback channel {new_channel}.')

            modified_track = mido.MidiTrack()

            for msg in track:
                if not msg.is_meta and hasattr(msg, 'channel'):
                    modified_msg = msg.copy(channel=new_channel)
                else:
                    modified_msg = msg.copy()
                modified_track.append(modified_msg)

            modified_midi.tracks.append(modified_track)

        modified_midi.save(path_to_midi_final)

    def generate_midi_files(self):
        self.log.debug('Entering generate_midi_files')
        self.delete_everything_in_folders()
        self.generate_chords_and_melody()
        self.generate_bass()
        self.generate_drums()
        self.generate_structure()

    def append_midi(self, midi_list):
        self.log.debug('Entering append_midi')
        if not midi_list:
            raise ValueError("At least one MIDI file is required.")

        concatenated_midi = pretty_midi.PrettyMIDI()

        for midi in midi_list:
            for instrument in midi.instruments:
                new_instrument = pretty_midi.Instrument(program=instrument.program, is_drum=instrument.is_drum)

                new_instrument.notes = instrument.notes
                new_instrument.pitch_bends = instrument.pitch_bends
                new_instrument.control_changes = instrument.control_changes

                concatenated_midi.instruments.append(new_instrument)

        return concatenated_midi

    def concatenate_midi(self, midifiles):
        """
        Concatenates multiple MIDI files using pretty_midi and saves the result.

        Args:
        - midi_paths (list): List of paths to MIDI files.
        - output_path (str): Path to save the concatenated MIDI.
        """

        concatenated_midi = pretty_midi.PrettyMIDI()

        current_offset = 0.0

        for midi in midifiles:
            for instrument in midi.instruments:
                for note in instrument.notes:
                    note.start += current_offset
                    note.end += current_offset

                concatenated_midi.instruments.append(instrument)

            current_offset += 8

        return concatenated_midi

    def get_total_time(self, midifile):
        # Defino para deducir duracion de midifiles
        total_steps = int(self.num_steps)
        steps_per_bar = 16
        ticks_per_beat = midifile.ticks_per_beat  # Magenta genera midis con esta cantidad de ticks per beat
        ticks_per_step = ticks_per_beat / 4

        number_of_bars = total_steps / steps_per_bar

        total_ticks = number_of_bars * steps_per_bar * ticks_per_step
        return total_ticks

    def extract_single_channel(self, midi_filename, channel_to_keep):
        """
        Extracts a single channel from a MIDI file and creates a new MIDI file.

        Args:
            midi_filename (str): Path to the original MIDI file.
            channel_to_keep (int): The channel number to keep (0-indexed).

        Returns:
            mido.MidiFile: A new MIDI file containing only the specified channel's messages.
        """
        original_midi = mido.MidiFile(midi_filename)
        new_midi = mido.MidiFile(ticks_per_beat=original_midi.ticks_per_beat)

        for track in original_midi.tracks:
            new_track = mido.MidiTrack()
            time_offset = 0

            for msg in track:
                if msg.type == 'note_on' or msg.type == 'note_off':
                    if msg.channel == channel_to_keep:
                        new_msg = msg.copy(time=msg.time + time_offset)
                        new_track.append(new_msg)

                elif msg.type == 'set_tempo':
                    time_offset += msg.time
                    new_msg = msg.copy(time=0)
                    new_track.append(new_msg)

            if new_track:
                new_midi.tracks.append(new_track)

        return new_midi

    def generate_bass(self):
        self.log.debug('Entering generate_bass')
        os.makedirs(self.bass_path, exist_ok=True)
        bundle_file = self.chords_bundle
        output_dir = self.bass_path
        num_outputs = self.num_outputs
        backing_chords = self.backing_chords
        primer_melody = self.bass_primer_melody
        temperature = self.bass_temperature

        for i in range(num_outputs):
            cmd = 'improv_rnn_generate --config=chord_pitches_improv --bundle_file="{}" --output_dir={} ' \
                  '--num_outputs={} --primer_melody="{}" --temperature={} --backing_chords="{}" ' \
                  '--render_chords'.format(bundle_file, output_dir, 1, primer_melody, temperature, backing_chords[i])
            os.system(cmd)
            self.log.debug('cmd: ' + cmd)

        files = [i for i in os.listdir(self.bass_path)]
        for file in files:
            new_bass = mido.MidiFile()
            midi_filename = self.bass_path+'/'+file
            new_bass = self.extract_single_channel(midi_filename=midi_filename, channel_to_keep=0)
            new_bass = self.change_channels_of_one_file(new_bass, self.bass_channel)
            new_bass.save(midi_filename)

    def delete_everything_in_folders(self):
        self.log.debug('Entering delete_everything_in_folders')
        folder_paths = [self.bass_path, self.drum_path, self.chords_path, self.melody_path]
        for path in folder_paths:
            try:
                files = [os.path.join(path, file) for file in os.listdir(path) if
                         os.path.isfile(os.path.join(path, file))]

                for file in files:
                    os.remove(file)

            except Exception as e:
                self.log.exception("An error occurred deleting from folder {}: {}".format(path, str(e)))

    def generate_drums(self):
        """
        Generate drum MIDI files using a pre-trained Magenta model for each bass file.

        Parameters: None

        Returns: None

        Description:
            The function generates drum MIDI files using a pre-trained model for each bass file found in the
            'self.bass_path' directory. The MIDI generation is based on the provided configuration and parameters in
            the config.py file.

            The function uses the 'drums_rnn_generate' command-line tool from the Magenta project. The pre-trained model
            is specified by 'drum_bundle'.

            For each bass file found in the 'self.bass_path' directory, a corresponding drum MIDI file will be
            generated. The generated drum MIDI files will be saved in the 'drum_path' directory. The 'num_outputs'
            parameter is set to 1 for each bass file, meaning one drum MIDI file will be generated for each bass file.

            The 'num_steps' parameter determines the length of the generated drum MIDI files.
        """
        self.log.debug('Entering generate_drums')
        os.makedirs(self.bass_path, exist_ok=True)
        files = [i for i in os.listdir(self.bass_path)]
        num_outputs = 1  # one for each bass file
        checkpoint_file = self.drum_checkpoint
        output_dir = self.drum_path
        temperature = self.drum_temperature

        for file in files:
            cmd = 'music_vae_generate --config=groovae_4bar --checkpoint_file={} --mode=sample --num_outputs={}' \
                  ' --output_dir={} --temperature={}'.format(checkpoint_file, num_outputs, output_dir, temperature)
            os.system(cmd)
            self.log.debug('cmd ' + cmd)

    def generate_chords_and_melody(self):
        self.log.debug('Entering generate_chords_and_melody')
        os.makedirs(self.chords_path, exist_ok=True)
        os.makedirs(self.melody_path, exist_ok=True)

        bundle_file = self.chords_bundle
        output_dir = self.chords_path
        num_outputs = self.num_outputs
        backing_chords = self.backing_chords
        primer_melody = self.melody_primer_melody

        for i in range(num_outputs):
            cmd = 'improv_rnn_generate --config=chord_pitches_improv --bundle_file="{}" --output_dir={} ' \
                  '--num_outputs={} --primer-melody="{}" --backing_chords="{}" --render_chords'.format(bundle_file, output_dir, 1,
                                                                                                       primer_melody[i], backing_chords[i])
            os.system(cmd)
            self.log.debug('cmd: ' + cmd)

        files = [i for i in os.listdir(self.chords_path)]
        for file in files:
            new_chords = mido.MidiFile()
            midi_filename = self.chords_path+'/'+file

            new_melody = self.extract_single_channel(midi_filename=midi_filename, channel_to_keep=0)
            new_melody = self.change_channels_of_one_file(new_melody, self.melody_channel)
            new_melody.save(f'{self.melody_path}/{file}')

            new_chords = self.extract_single_channel(midi_filename=midi_filename, channel_to_keep=1)
            new_chords = self.change_channels_of_one_file(new_chords, self.chords_channel)
            new_chords.save(f'{self.chords_path}/{file}')

    def generate_structure(self):
        """
        Generate the structure of the final MIDI files using different instruments.

        Parameters: None

        Returns: None

        Description:
            The function generates the structure of the final MIDI file with different instruments based on the provided
             paths and MIDI structure from config.py

            The function initializes a dictionary 'midi_dict' that will store the file assignments for each instrument
            and each value in the 'midi_structure'. The instruments are defined as ['bass', 'drum', 'melody', 'chords'].

            For each folder path (bass_path, drum_path, melody_path, chords_path), the function retrieves the files
            using the 'get_files_from_folder' helper function. The files are sorted in alphabetical order.

            The 'midi_dict' is populated by assigning files to each value in order from each folder. For example,
            if 'bass_path' exists, the bass files will be assigned to each value in the 'midi_structure' in order.

            After populating 'midi_dict', the function creates a list of instruments in order
            ('list_instruments_in_order') by concatenating the MIDI files in the order defined in 'midi_structure' for
            each instrument. The 'concat_midi' method is used for concatenation.

            Finally, the 'append_midi' method is called to create a new MIDI file that combines the concatenated MIDI
            files of different instruments resulting in a MIDI file with one instrument per track.
        """
        self.log.debug('Entering generate_structure')
        bass_path = self.bass_path
        drum_path = self.drum_path
        melody_path = self.melody_path
        chords_path = self.chords_path
        midi_structure = self.midi_structure

        def get_files_from_folder(folder_path):
            files = os.listdir(folder_path)
            return sorted([file for file in files if os.path.isfile(os.path.join(folder_path, file))])

        instruments = self.instruments
        midi_dict = {value: {instrument: '' for instrument in instruments} for value in set(midi_structure)}
        # midi_dict example:
        # {
        #     'A': {'bass': '', 'drum': '', 'melody': '', 'chords': ''},
        #     'B': {'bass': '', 'drum': '', 'melody': '', 'chords': ''},
        #     'C': {'bass': '', 'drum': '', 'melody': '', 'chords': ''}
        # }

        # Este diccionario tiene que estar en el mismo orden que los instrumentos. Con esto se asignan mas adelante
        # los channels a cada parte de la estructura.
        channel_assignments = {
            'track0': 0,
            'bass': self.bass_channel,
            'drums': self.drums_channel,
            'melody': self.melody_channel,
            'chords': self.chords_channel,
        }

        if os.path.exists(bass_path):
            files_bass = get_files_from_folder(bass_path)
            for i, value in enumerate(set(midi_structure)):
                midi_dict[value][instruments[0]] = bass_path + '/' + files_bass[i]

        if os.path.exists(drum_path):
            files_drum = get_files_from_folder(drum_path)
            for i, value in enumerate(set(midi_structure)):
                midi_dict[value][instruments[1]] = drum_path + '/' + files_drum[i]

        if os.path.exists(melody_path):
            files_melody = get_files_from_folder(melody_path)
            for i, value in enumerate(set(midi_structure)):
                midi_dict[value][instruments[2]] = melody_path + '/' + files_melody[i]

        if os.path.exists(chords_path):
            files_chords = get_files_from_folder(chords_path)
            for i, value in enumerate(set(midi_structure)):
                midi_dict[value][instruments[3]] = chords_path + '/' + files_chords[i]

        for k in midi_dict:     # Para cada letra (A, B, C...)
            midis_to_append = []
            for instrument in instruments:
                midi = pretty_midi.PrettyMIDI(midi_dict[k][instrument])     # midi_dict[k][instrument]
                midis_to_append.append(midi)
            midis_appended = self.append_midi(midis_to_append)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_folder = f"{self.path_to_midis_for_structure}"
            os.makedirs(output_folder, exist_ok=True)
            filename = f"{output_folder}/{k}_{timestamp}.mid"
            midis_appended.write(filename)

        folder_path = self.path_to_midis_for_structure
        file_list = os.listdir(folder_path)
        for filename in file_list:
            if os.path.isfile(os.path.join(folder_path, filename)):
                path_final = os.path.join(folder_path, filename)
                output_string = path_final.replace("\\", "/")
                self.change_channels_of_tracks(output_string, list(channel_assignments.values()))

        list_instruments_in_order = []
        for instrument in instruments:
            midis_to_concat = []
            for i in config.MIDI_STRUCTURE:
                midi = pretty_midi.PrettyMIDI(midi_dict[i][instrument])
                midis_to_concat.append(midi)
            midis_concatenated = self.concatenate_midi(midis_to_concat)
            list_instruments_in_order.append(midis_concatenated)

        # append midis
        midi_final_file = mido.MidiFile()
        midi_final_file = self.append_midi(list_instruments_in_order)

        os.makedirs(self.midi_final, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{self.midi_final}/midi_final{timestamp}.mid"
        midi_final_file.write(filename)

        folder_path = self.midi_final
        file_list = os.listdir(folder_path)
        for filename in file_list:
            if os.path.isfile(os.path.join(folder_path, filename)):
                path_final = os.path.join(folder_path, filename)
                output_string = path_final.replace("\\", "/")
                self.change_channels_of_tracks(output_string, list(channel_assignments.values()))

