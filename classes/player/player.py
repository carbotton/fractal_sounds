import datetime
import os
import shutil
import random
from classes.logger.logger import Logger
import classes.player.player_config as config_player
import classes.config as config
import mido
from mido import MidiFile
import os
import math

from dto.parameters_dto import ParametersDto
from classes.logger.logger import Logger
import classes.player.player_config as config_player
import mido
from mido import MidiFile
import os
from pythonosc import udp_client

from dto.parameters_dto import ParametersDto
from classes import config
from time import sleep

import os



class Player:
    """
    This class is responsible for playback, receiving notes, and using parameters that affect playback.
    """
    def __init__(self, shared_memory: ParametersDto):
        self.sm = shared_memory
        self.open_ports = []
        self.outport = config_player.LOOPMIDI_PORT
        self.midi_structure = config.MIDI_STRUCTURE
        self.path_to_midis_for_structure = config.PATH_TO_MIDIS_FOR_STRUCTURE
        self.path_to_midis_processed = config.PATH_TO_MIDIS_PROCESSED
        self.log = Logger("Player", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.reaper_ip = config_player.REAPER_IP
        self.reaper_port = config_player.REAPER_PORT_OSC


    def close_midi_ports(self):
        for port in self.open_ports:
            port.close()
        self.open_ports = []

    def setup_midi_port(self):
        return self.outport

    def switch_instrument_track(self):
        pass

    def change_track_volume(self):
        pass


    def modify_velocity(self, msg, velocity_value):
        """
        Modifies the velocity value of the MIDI message.
        Velocity values must be integers between 0 (note-off) and 127 (maximum intensity).

        :param msg: MIDI message.
        :param velocity_value: Desired velocity value (0-127).
        :return: Modified MIDI message.
        """


        if hasattr(msg, 'velocity'):

            if msg.channel == 9 and velocity_value < msg.velocity:

                change_drums_velocity_enable = True
            else:
                change_drums_velocity_enable = False

            if msg.velocity != 0 and (msg.channel != 9 or change_drums_velocity_enable):

                if velocity_value>127:
                    velocity_value=127
                if velocity_value<0:
                    velocity_value=0
                msg.velocity = int(velocity_value)

        return msg

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

    def change_note(self, msg, note_value):
        """
        Modifies the note value of the MIDI message.
        Note values must be integers between 0 (C-1) and 127 (G9).

        :param msg: MIDI message.
        :param note_value: Desired note value (0-127).
        :return: Modified MIDI message.
        """
        if hasattr(msg, 'note'):
            msg.note = note_value
        return msg

    def modify_time(self, msg, time_value):
        """
        Modifies the time delay of the MIDI message.
        Time values are typically floats, representing delay in seconds.

        :param msg: MIDI message.
        :param time_value: Desired time delay (float in seconds).
        :return: Modified MIDI message.
        """
        if hasattr(msg, 'time'):
            msg.time = time_value
        return msg

    def transpose_note_in_scale(self, msg, scale=[0, 2, 4, 5, 7, 9, 11, 12], transpose_value=0):
        """
        Transposes a note within a scale.
        Note values must be integers between 0 (C-1) and 127 (G9).
        Transpose values should be integers, indicating the number of scale steps to transpose.
        The scale is represented as a list of integers, representing the notes in the scale
        relative to the root note of 0.

        :param msg: MIDI message.
        :param scale: The scale to transpose within, e.g., [0, 2, 4, 5, 7, 9, 11, 12] for the major scale.
        :param transpose_value: The number of scale steps to transpose. Can be negative to transpose down.
        :return: Modified MIDI message.
        """
        if hasattr(msg, 'note'):
            note = msg.note % 12  # Get the note relative to C
            if note in scale:
                scale_index = scale.index(note)
                transposed_index = (scale_index + transpose_value) % len(scale)
                octave = msg.note // 12  # Get the current octave
                # Calculate new note, taking into account the octave and ensuring it stays within the valid MIDI range
                transposed_note = max(0, min(127, octave * 12 + scale[transposed_index]))
                msg.note = transposed_note
        return msg

    def modify_pitch(self, msg, pitch_value):
        """
        Modifies the pitch bend value of the MIDI message.

        :param msg: MIDI pitch bend message.
        :param pitch_value: Desired pitch bend value (usually -8192 to 8191).
        :return: Modified MIDI pitch bend message.
        """
        if hasattr(msg, 'pitch'):
            msg.pitch = int(pitch_value)
        return msg

    def modify_emotion(self, msg, emotion_value):
        if int(emotion_value) > config.HAPPY_SONG:
            msg = self.modify_velocity(msg, 90)
            if hasattr(msg, 'pitch'):
                msg.pitch = int(msg.pitch*emotion_value/10)
        elif int(emotion_value) < config.SAD_SONG:
            msg = self.modify_velocity(msg, 40)
            if hasattr(msg, 'pitch'):
                msg.pitch = int(msg.pitch/4)
        return msg

    def solo_track(self, value):
        solo = None
        if value > 0 and value < 60:
            solo = 0
        else:
            solo = 1
        client = udp_client.SimpleUDPClient(self.reaper_ip, self.reaper_port)
        track_number = 1
        osc_address = f"/track/{str(track_number)}/solo"
        client.send_message(osc_address, solo)  # 1 for solo, 0 for unsolo

    def toggle_reaper_fx(self, track_number, fx_number, enable):
        """
        Toggles an effect on a specific track in Reaper.

        Parameters:
        ip (str): The IP address of the OSC server (Reaper).
        port (int): The port number for the OSC server.
        track_number (int): The track number.
        fx_number (int): The FX slot number on the track (starting from 1 for the first effect).
        enable (bool): True to enable the effect, False to disable.
        """
        client = udp_client.SimpleUDPClient(self.reaper_ip, self.reaper_port)
        address = f"/track/{track_number}/fx/{fx_number}/bypass"
        value = 1 if enable else 0  # 0 to enable, 1 to disable
        client.send_message(address, value)

    def pan_reaper_track(self, track_number, pan_value):
        """
        Pans a track in Reaper based on the provided value.

        Parameters:
        track_number (int): The track number to pan.
        pan_value (float): The value to determine the pan position.
                           0 for fully left, 0.5 for center, and 1 for fully right.

        The pan value in Reaper ranges from -1 (fully left) to 1 (fully right),
        so we need to map the input range (0 to 1) to this range.
        """
        client = udp_client.SimpleUDPClient(self.reaper_ip, self.reaper_port)

        reaper_pan_value = 1 - pan_value  # Espejamos el paning

        self.log.debug(f'Panning = {reaper_pan_value}')

        address = f"/track/{track_number}/pan"

        client.send_message(address, reaper_pan_value)

    def set_reaper_track_volume(self, track_number, volume_value):
        """
        Sets the volume for a specific track in Reaper.

        Parameters:
        track_number (int): The track number to set the volume for.
        volume_value (float): The volume level to set for the track.
                              Should be between 0.0 (silence) and 1.0 (unity gain),
                              but can potentially be higher for gain boost.

        Reaper uses a value between 0.0 and 1.0 for volume control,
        where 0.0 is silence and 1.0 represents unity gain. Values above 1.0
        may be used for gain boost depending on Reaper's configuration.
        """
        client = udp_client.SimpleUDPClient(self.reaper_ip, self.reaper_port)

        address = f"/track/{track_number}/volume"

        client.send_message(address, volume_value)

    def update(self, msg, velocity):
        msg = self.modify_velocity(msg, velocity)  # Set velocity to 100
        # msg = self.modify_pitch(msg, self.sm[config.PITCH])
        # msg = self.modify_emotion(msg, self.sm[config.EMOTION])
        # msg = self.modify_channel(msg, self.sm.channel)  # Set channel to 1
        msg = self.transpose_note_in_scale(msg=msg, transpose_value=self.sm[config.PITCH])  # Set note to 60 (Middle C)
        # msg = self.modify_time(msg, 1.0)  # Set time to 1.0 second
        # self.solo_track(self.sm[config.VELOCITY])
        cursor = self.sm['cursor_position'][0]
        gesto = self.sm['cursor_position'][1]
        if cursor:
            if gesto == "mano izquierda":
                self.modify_volume_of_reaper_tracks(cursor)

            self.modify_pan_of_reaper_tracks(cursor)
        return msg

    def modify_pan_of_reaper_tracks(self,cursor):


        if len(cursor) > 0:
            ##### PAN CONTROL
            pan_value = cursor[0]
            self.pan_reaper_track(track_number=5, pan_value=pan_value)
            ####################

    def modify_volume_of_reaper_tracks(self,cursor):


        if len(cursor) > 1:

            # Escalamos mano para que a posicion 0.5 hallan -6dB
            # Y para que posicion 1 sea 0dB
            track_number = 6
            volume_value = cursor[1] * (-0.98 * cursor[1] + 1.67)
            #volume_value = 0.5 * (-0.98 * 0.5 + 1.67)
            self.set_reaper_track_volume(track_number, volume_value)

            # Inversa
            track_number = 7
            #volume_value = 0.5 * (-0.98 * 0.5 + 0.29) + 0.69
            volume_value = cursor[1] * (-0.98 * cursor[1] + 0.29) + 0.69
            self.set_reaper_track_volume(track_number, volume_value)

    def change_fx(self, current_part):
        self.log.debug('Entrando a change_fx')
        if current_part == 'A':
            # Cambiamos bajo
            track_number = 1
            self.toggle_reaper_fx(track_number, 2, True)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 4, False)  # Enable the first effect on track 4
            track_number = 8
            self.toggle_reaper_fx(track_number, 2, True)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 4, False)  # Enable the first effect on track 4

            # Cambiamos melody
            track_number = 3
            self.toggle_reaper_fx(track_number, 1, True)
            self.toggle_reaper_fx(track_number, 2, False)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Disable the second effect on track 4
            track_number = 10
            self.toggle_reaper_fx(track_number, 1, True)
            self.toggle_reaper_fx(track_number, 2, False)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Disable the second effect on track 4

        elif current_part == 'B':
            # Cambiamos bajo
            track_number = 1
            self.toggle_reaper_fx(track_number, 2, False)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 3, True)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 4, False)  # Enable the first effect on track 4
            # Cambiamos bajo
            track_number = 8
            self.toggle_reaper_fx(track_number, 2, False)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 3, True)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 4, False)  # Enable the first effect on track 4

            # Cambiamos melody
            track_number = 3
            self.toggle_reaper_fx(track_number, 1, False)
            self.toggle_reaper_fx(track_number, 2, True)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Disable the second effect on track 4
            track_number = 10
            self.toggle_reaper_fx(track_number, 1, False)
            self.toggle_reaper_fx(track_number, 2, True)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Disable the second effect on track 4

        elif current_part == 'C':
            # Cambiamos bajo
            track_number = 1
            self.toggle_reaper_fx(track_number, 2, False)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 4, True)  # Enable the first effect on track 4
            track_number = 8
            self.toggle_reaper_fx(track_number, 2, False)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 3, False)  # Disable the second effect on track 4
            self.toggle_reaper_fx(track_number, 4, True)  # Enable the first effect on track 4

            # Cambiamos melody
            track_number = 3
            self.toggle_reaper_fx(track_number, 1, False)
            self.toggle_reaper_fx(track_number, 2, True)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 3, True)  # Disable the second effect on track 4
            track_number = 10
            self.toggle_reaper_fx(track_number, 1, False)
            self.toggle_reaper_fx(track_number, 2, True)  # Enable the first effect on track 4
            self.toggle_reaper_fx(track_number, 3, True)  # Disable the second effect on track 4

    def get_song_parts(self, midi_structure_enum, directory_path):
        letters = list(set(letter for index, letter in midi_structure_enum))    # (A, B, C)
        files_dict = {letter: None for letter in letters}    # {'A':None, 'B':None, 'C':None}

        files = os.listdir(directory_path)
        files.sort()
        for file in files:
            prefix = file.split('_')[0]
            if prefix in files_dict and files_dict[prefix] is None:
                files_dict[prefix] = os.path.join(directory_path, file)
                files_dict[prefix].replace("\\", "/")

        return files_dict

    def main(self):
        midi_structure_enum = list(enumerate(self.midi_structure))
        file_path = f"{self.path_to_midis_for_structure}"
        processed_file_path = f"{self.path_to_midis_processed}"
        current_part = midi_structure_enum[0][1]
        current_index = midi_structure_enum[0][0]
        part_counter = 2    # Contador para reproducir AA BB CC
        self.log.debug(f'Current part: {current_part}. Current index: {current_index}')

        song_parts = self.get_song_parts(midi_structure_enum, file_path)
        self.log.debug(f'Song parts = {song_parts}')

        # List available MIDI output ports
        output_ports = mido.get_output_names()
        self.log.debug("\nAvailable MIDI Output Ports:")
        for port in output_ports:
            self.log.debug(port)

        outport = mido.open_output(str(config_player.LOOPMIDI_PORT))
        note_duration =0
        time_since_last_note = 0

        self.last_note=127
        velocity = 127

        while not self.sm['exit']:
            self.sm['ready_to_recive_midi_note'] = False

            file = song_parts.get(current_part)
            self.log.info(f'Playing the file {file}')

            #midi_file_path = file.replace("\\", "/")
            #self.log.debug(f'midi_file_path = {midi_file_path}')
            mid = MidiFile(file)

            if self.sm['exit']:
                break
            try:

                for msg in mid.play():  # Separate by channels
                    if self.sm['exit'] or self.sm['song_ended']:
                        break
                    if not msg.is_meta:

                        msg = self.update(msg, velocity)
                        #self.log.debug(f'Sending message {msg}')

                        outport.send(msg)  # Send the message using the first open port

                        time_since_last_note += msg.time
                        if time_since_last_note >= note_duration and self.sm["send_note"]:
                            additional_note=self.sm["fractal_note_dict"]["note"] #este dict ya esta cargado por que las send_note
                            additional_note_velocity=self.sm["fractal_note_dict"]["velocity"]
                            additional_note_channel=self.sm["fractal_note_dict"]["channel"]
                            additional_note_duration=self.sm["fractal_note_dict"]["note_duration"]


                            new_note_off = mido.Message('note_on', note=self.last_note, velocity=0,
                                                        time=additional_note_duration, channel=additional_note_channel)
                            outport.send(new_note_off)

                            new_note_on = mido.Message('note_on', note=additional_note, velocity=additional_note_velocity, time=0,
                                                       channel=additional_note_channel)
                            outport.send(new_note_on)

                            self.log.debug(f'Sending new_note_on {new_note_on}')
                            self.log.debug(f'Sending new_note_off {new_note_off}')


                            note_duration = additional_note_duration
                            time_since_last_note = 0
                            self.sm['ready_to_recive_midi_note'] = True
                            self.last_note = additional_note
                        else:
                            self.sm['ready_to_recive_midi_note'] = False

            except Exception as e:
                self.log.exception(f"Exception occurred: {str(e)}")
                self.close_midi_ports()

            part_counter -= 1
            if part_counter == 0:   # Ya repeti esta parte, voy a la siguiente
                part_counter = 2
                current_index += 1
                if current_index > len(midi_structure_enum) - 1:
                    self.log.info('Song ended... Starting over :)')
                    current_part = midi_structure_enum[0][1]
                    current_index = midi_structure_enum[0][0]

                else:
                    current_part = midi_structure_enum[current_index][1]

                    self.log.debug('Next part: '.format(current_part))

            el_usuario_se_movio = self.sm[config.CHANGE_DETECTED]
            if el_usuario_se_movio:
                self.sm['song_ended'] = False
                if velocity <= 0:   # CHANGE SONG -- NEW EXPERIENCE

                    self.log.info('User left. Selecting new song...')
                    for song in song_parts.values():
                        if os.path.exists(file_path):
                            os.makedirs(processed_file_path, exist_ok=True)
                            destination_file = os.path.join(processed_file_path, os.path.basename(song))
                            shutil.move(song, destination_file)
                            self.log.debug(f"Moved: {song}")
                        else:
                            self.log.warning(f"File not found: {song}")
                    song_parts = self.get_song_parts(midi_structure_enum, file_path)

                self.sm[config.CHANGE_DETECTED] = False
                velocity = 127
            else:

                new_note_off = mido.Message('note_on', note=self.last_note, velocity=0,
                                            time=0, channel=8)
                outport.send(new_note_off)
                velocity = max(0, velocity-86)
                self.log.debug(f'Velocity changed to {velocity}...')
                if velocity==0:
                    self.sm['song_ended'] = True
                    self.sm["zoom_center_changed"]= True
                    # self.change_fx(current_part)
        self.close_midi_ports()
        self.log.info("Player has finished")