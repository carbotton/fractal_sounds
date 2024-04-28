from multiprocessing import Manager
from classes import config
manager = Manager()
class SharedMemory:
    """
       A class to explore fractals using CUDA accelerated generation and interactive zoom.
       """
    def __init__(self):
        shared_memory = manager.dict()

        shared_memory['velocity'] = 100
        shared_memory['tempo'] = None
        shared_memory['pitch'] = 0
        shared_memory['volume'] = None
        shared_memory['midi'] = None
        shared_memory['is_minor'] = None
        shared_memory['emotion'] = 1
        shared_memory['fractal_frame'] = None
        shared_memory['arrow_params'] = None
        shared_memory['width'] = config.WIDTH
        shared_memory['height'] = config.HEIGHT
        shared_memory["zoom_center_changed"] = False
        shared_memory["click_x"]=None
        shared_memory["click_y"]=None
        shared_memory["color_iter"]=831
        shared_memory["array_of_points"] = []
        shared_memory['exit'] = False
        shared_memory['change_detected'] = False
        shared_memory['send_note'] = False
        shared_memory['ready_to_recive_midi_note'] = False
        shared_memory['fractal_note_dict'] = []
        shared_memory['fractal_player_finish'] = False
        shared_memory['note_velocity'] =1
        shared_memory['cursor_position'] = [(0,0),"dibujando"]
        shared_memory['rgb'] = []
        shared_memory['song_ended'] = False
        self.shared_memory=shared_memory