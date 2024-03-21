from classes.logger.logger import Logger


class ParametersDto:
    def __init__(self, velocity=20, tempo=20, pitch=20, volume=20, midi=20, emotion=20, is_minor:bool=None, change_detected=False, array_of_points=[]):
        self.log = Logger("ParametersDto").logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.velocity = velocity
        self.tempo = tempo
        self.pitch = pitch
        self.volume = volume
        self.is_minor = is_minor
        self.midi = midi
        self.emotion = emotion
        self.change_detected = change_detected
        self.array_of_points = array_of_points
