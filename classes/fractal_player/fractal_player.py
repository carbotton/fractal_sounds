import threading
import random

import cv2
import mido
import time
import classes.config as config
import classes.player.player_config as player_config
from dto.parameters_dto import ParametersDto
from classes.logger.logger import Logger

class Fractal_Player():

    def __init__(self, shared_memory: ParametersDto):
        self.log = Logger("Fractal Player", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.sm = shared_memory
        self.outport = mido.open_output(player_config.LOOPMIDI_PORT)
        self.prev_x = 0
        self.prev_y = 0
        self.width = shared_memory['width']
        self.height = shared_memory['height']
        self.log = Logger("Fractal Player", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.max_length_note_array= config.MAX_LENGTH_NOTE_ARRAY
    def rgb_to_midi(self, r, g, b):
        r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
        total_intensity = r_norm + g_norm + b_norm
        if total_intensity == 0:
            return 0

        red_contribution = (r_norm / total_intensity) * 95
        green_contribution = (g_norm / total_intensity) * 64
        blue_contribution = (b_norm / total_intensity) * 32

        return int(red_contribution + green_contribution + blue_contribution)

    def map_to_a_major(self, pitch, root_note=36):
        pitch_class = (pitch - root_note) % 12
        scale_degrees = [0, 2, 4, 5, 7, 9, 11,12,14,16,17,19,21,23,24]
        closest_scale_degree = min(scale_degrees, key=lambda x: abs(x - pitch_class))
        return (pitch - pitch_class) + closest_scale_degree

    def get_note_name(self, midi_note):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12
        return f'{note_names[note_index]}{octave}'

    def send_midi_note(self, note):
        velocity = random.randint(80, 120)
        note_duration = 0.125
        channel=config.FRACTAL_CHANNEL
        self.sm["fractal_note_dict"] = {"note":note, "velocity":velocity, "channel":channel, "note_duration":note_duration}
        self.sm["send_note"]=True

        while not self.sm['ready_to_recive_midi_note']: #esperas por la proxima nota
            if self.sm['exit']:
                break
            continue
        self.sm['ready_to_recive_midi_note']= False
        self.sm["send_note"]=False

    def transformar_a_coordenadas_absolutas(self, x0, y0, x1, y1, x_size, y_size):
        '''
        Pasa de coordenas relativas a absolutas
        Args:
            x0:
            y0:
            x1:
            y1:
            x_size: tamaño de la imagen en el eje horizontal
            y_size: tamaño de la imagen en el eje vertical

        Returns:

        '''
        x0 = int(x_size*x0)
        y0 = int(y_size*y0)

        x1 = int(x_size * x1)
        y1 = int(y_size * y1)

        return x0, y0, x1, y1

    def process_image(self, points, steps=5, channel=8):
        x_size = self.width
        y_size = self.height

        x0, y0 = points[-1]

        x0 = int(x_size * (1-x0))
        y0 = int(y_size * y0)

        frame=self.sm['fractal_frame']

        x, y = int(min(x0, x_size - 1)), int(min(y0, y_size - 1))
        r, g, b = frame[y, x][2], frame[y, x][1], frame[y, x][0]
        self.colores.append((r, g, b))

        self.sm['rgb']=self.colores

        midi_note = self.rgb_to_midi(r, g, b) #depende del frame
        mapped_midi_note = self.map_to_a_major(midi_note)

        self.log.debug(f'Pixel at ({x}, {y}): MIDI note {self.get_note_name(mapped_midi_note)}')
        self.send_midi_note(mapped_midi_note)

        self.sm["click_x"], self.sm["click_y"] = x, y

    def main(self):
        self.current_array_length=0
        self.colores = []
        while True:
            len_of_array=len(self.sm['array_of_points'])

            if len_of_array> self.current_array_length:
                self.current_array_length = len_of_array
                self.process_image(self.sm['array_of_points'], steps=config.STEPS)
            if len_of_array < self.current_array_length:
                self.current_array_length=0

            if self.sm['exit']:
                break
        self.log.info("fractal players has finished")