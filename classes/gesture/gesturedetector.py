import cv2
import joblib
import mediapipe as mp
import numpy as np
import xgboost as xgb
import pandas as pd

from classes import config
from classes.config import MAX_LENGTH_NOTE_ARRAY
from classes.logger.logger import Logger


class GestureDetector:
    def __init__(self, smoothing_factor=5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.mp_draw = mp.solutions.drawing_utils
        self.last_gestures = []
        self.smoothing_factor = smoothing_factor

        # Atributos de deteccion
        self.index_finger_array = []
        self.flag_of_detection = None
        self.elapsed_time = None

        self.model = xgb.Booster()
        self.model.load_model('source/modelo_entrenado.json')

        # Cargar el LabelEncoder previamente guardado
        self.label_encoder = joblib.load('source/label_encoder.pkl')
        self.model.set_param({'predictor': 'gpu_predictor'})

        self.max_length_note_array=MAX_LENGTH_NOTE_ARRAY
        self.log = Logger("GestureDetector", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')

        self.previous_bounding_box_sizes = [0, 0]   # ZOOM
        self.last_position_detected=[0, 0]

    def hands_approaching(self, gestures, landmarks,current_sizes):

        size = self.calculate_bounding_box_size(landmarks)  # ZOOM
        current_sizes.append(size)  # ZOOM

        if len(gestures) >= 2 and {"mano izquierda", "mano derecha"}.issubset(
                gestures):  # un gesto es mano izquierda y ademas hay otro mas
            if len(self.previous_bounding_box_sizes) < 2:
                self.previous_bounding_box_sizes = [0, 0]

            hands_approaching = all(
                curr > prev+0.2 for curr, prev in zip(current_sizes, self.previous_bounding_box_sizes))
            self.previous_bounding_box_sizes = current_sizes
            return hands_approaching

    def gesture_classification(self,hand_landmarks):
        def extract_landmarks_dataframe(landmarks):
            # Crear una lista con los nombres de las columnas
            columns = [f"lm_{i}_{axis}" for i in range(21) for axis in ['x', 'y', 'z']]
            # Extraer los valores de los landmarks
            values = np.array([[landmark.x, landmark.y, landmark.z] for landmark in landmarks.landmark]).flatten()
            # Crear y devolver un DataFrame con una sola fila y los nombres de columnas correctos
            return pd.DataFrame([values], columns=columns)

        # Utilizar la función modificada para extraer landmarks y convertirlos en un DataFrame
        landmarks_df = extract_landmarks_dataframe(hand_landmarks)

        # Ahora convertir el DataFrame a DMatrix
        dmatrix_data = xgb.DMatrix(landmarks_df)

        # Hacer la predicción con el modelo
        y_pred_probs = self.model.predict(dmatrix_data)

        y_pred = np.argmax(y_pred_probs, axis=1)
        y_pred_label = self.label_encoder.inverse_transform(y_pred)


        return y_pred_label[0]

    def detect_gesture(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb_frame)
        speed_rating=1
        current_gesture = None
        current_position = []
        velocity = None
        self.previus_distance = 0.05

        current_sizes = []
        gestures = []
        hands_approaching = False

        if results.multi_hand_landmarks:
            for landmarks in results.multi_hand_landmarks:

                current_position = self.calculate_centroid(landmarks)
                current_gesture = self.gesture_classification(landmarks)

                gestures.append(current_gesture)

                if len(self.index_finger_array) == 0:
                    self.index_finger_array.append(current_position)
                    self.last_position_detected=current_position
                last_position = self.index_finger_array[-1]


                distance = np.linalg.norm(np.array(last_position) - np.array(current_position))
                distance_velocity= np.linalg.norm(np.array(self.last_position_detected) - np.array(current_position))
                speed_rating = np.clip(int(distance_velocity/ 0.10 * 5), 1, 5)

                if distance > (self.previus_distance + (speed_rating / 50)):
                    self.previus_distance = distance
                    self.index_finger_array.append(current_position)

                self.last_position_detected=current_position
            hands_approaching = self.hands_approaching(gestures,landmarks,current_sizes)


        self.last_gestures.append(current_gesture)

        if len(self.last_gestures) > self.smoothing_factor:
            self.last_gestures.pop(0)

        if self.last_gestures.count(current_gesture) == self.smoothing_factor:
            return current_gesture, current_position, speed_rating, hands_approaching

        return current_gesture, current_position, speed_rating, hands_approaching

    def calculate_centroid(self, landmarks):
        x_list = [landmark.x for landmark in landmarks.landmark]
        y_list = [landmark.y for landmark in landmarks.landmark]
        centroid_x = sum(x_list) / len(x_list)
        centroid_y = sum(y_list) / len(y_list)
        return (centroid_x, centroid_y)


    def detect_index_finger_position(self, landmarks):
        index_finger_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        # Guardamos esto en un array de puntos
        self.current_index_finger_pos=(index_finger_tip.x, index_finger_tip.y)
        self.index_finger_array.append(self.current_index_finger_pos)
        self.log.info(f'detect_index_finger_position for {self.current_index_finger_pos}')
        self.log.info(f'detect_index_finger_position for {self.index_finger_array}')



    def release(self):
        self.hands.close()


    def calculate_bounding_box_size(self, landmarks):
        """
        Calculates the size of the bounding box that encloses all the landmarks of a detected hand in a frame.
        """
        x_min = min([landmark.x for landmark in landmarks.landmark])
        x_max = max([landmark.x for landmark in landmarks.landmark])
        y_min = min([landmark.y for landmark in landmarks.landmark])
        y_max = max([landmark.y for landmark in landmarks.landmark])

        width = x_max - x_min
        height = y_max - y_min
        return width * height


