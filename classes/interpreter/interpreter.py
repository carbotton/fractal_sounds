import time

from classes.config import VOLUME, CHANGE_DETECTED, COLOR_ITER, CAMERA_INDEX
from classes.gesture.gesturedetector import GestureDetector
from classes.logger.logger import Logger
from classes import config
from dto.parameters_dto import ParametersDto
import cv2


class Interpreter:
    """
          Esta clase se encarga de unir los inputs con los parametros manipulables
    """
    def __init__(self, shared_memory: ParametersDto):
        self.log = Logger("Interpreter", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.sm = shared_memory
        self.finger_postition: int=0
        self.is_smiling: bool = True
        self.detector = GestureDetector()
        self.width = shared_memory['width']
        self.height = shared_memory['height']

    def log_change(self, param_name):
        """
        Creates a callback for logging the value change of a parameter.

        :param param_name: The name of the parameter.
        :return: A callback function.
        """

        def callback(value):
            self.log.debug(f"{param_name} changed to {value}")

        return callback

    def main(self):
        self.log.info(f'Interpreter  main')
        self.arrows = []

        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        while True:
            ret, camera_frame = cap.read()

            if not ret:
                break

            prev_frame_time = time.time()

            gesture, position, note_velocity, hands_approaching = self.detector.detect_gesture(camera_frame)
            puntos = self.sm['array_of_points']
            new_frame_time = time.time()
            self.fps_actual = 1 / (new_frame_time - prev_frame_time)
            fps_text = f'FPS: {self.fps_actual:.2f}'

            if hands_approaching and len(puntos) and not self.sm["zoom_center_changed"] and not self.sm['doing_zoom']: # semaforo para parar el zoom
                position = puntos[-1]
                self.sm["click_x"] = int((1 - position[0]) * self.width)
                self.sm["click_y"] = int(position[1] * self.height)
                self.sm["zoom_center_changed"] = True
                self.sm['doing_zoom'] = True

            if self.sm["zoom_center_changed"]:
                self.log.info(f'zoom_center_changed borre todo')
                self.arrows = []
                self.sm['array_of_points'] = []
                self.sm['fractal_player_finish'] = False
                self.sm['rgb'] = []
                self.detector.index_finger_array = []

            if gesture is None:
                self.sm[CHANGE_DETECTED] = False

            if gesture and position:
                self.sm[CHANGE_DETECTED] = True  # con esto se sabe si el usuario se movio o no, para volumen de cancion
                self.update_sliders_based_on_gesture(gesture, position,camera_frame)

                cv2.putText(camera_frame, str(gesture) + fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2,
                            cv2.LINE_AA)
            else:
                cv2.putText(camera_frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        2,
                        cv2.LINE_AA)

            cv2.imshow('Gesture Detection', camera_frame)

            self.sm['array_of_points'] = self.detector.index_finger_array
            self.sm['note_velocity'] = note_velocity
            self.sm['cursor_position'] = [position,gesture]


            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.sm['exit'] = True

            if self.sm['exit']:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.detector.release()

        self.log.info("Interpreter has finished")
    def update_sliders_based_on_gesture(self, gesture, position,frame):
        _, position_y = position
        height, _, _ = frame.shape

        mapped_value = self.map_position_to_slider_value(position_y, height)

        if gesture == "mano derecha":
            self.log.debug(f' self.sm[COLOR_ITER] {gesture} previous {self.sm[COLOR_ITER]} new {mapped_value} ')
            self.sm[COLOR_ITER] = mapped_value

        elif gesture == "dibujando":
            self.sm[VOLUME] = mapped_value

    def map_position_to_slider_value(self, y, frame_height):
        slider_value = (1 - (y+0.1)) * 1503

        return int(slider_value)

    def user_moved(self, gesture):
        """
        Check if user movements are enough to consider new position

        Returns: True if user moved and False otherwise
        """
        if gesture is None:
            return False
        else:
            return True
