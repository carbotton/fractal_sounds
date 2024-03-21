
import time
from threading import Thread

from numba import cuda
import numpy as np
import cv2
import math

from classes import config
from classes.config import THREADS_PER_BLOCK
from classes.logger.logger import Logger
from itertools import cycle
import os

class FractalExplorer:
    """
       A class to explore fractals using CUDA accelerated generation and interactive zoom.
       """
    def __init__(self, shared_memory,width=1280, height=720,rotation_speed = 0.001,zoom_factor=0.991):
        """
                Initializes the FractalExplorer with default settings.

                Args:
                width (int): Width of the fractal window.
                height (int): Height of the fractal window.
                max_iter (int): Maximum iterations for fractal computation.
                rotation_speed (float): Speed of rotation for dynamic fractals.
                """
        self.width = width
        self.height = height
        self.const_max_inters=162
        self.max_iter = self.const_max_inters#162
        self.click_x, self.click_y = None, None
        self.zoom_center_changed = False
        self.x_min, self.x_max = -2.0, 1.0
        self.y_min, self.y_max = -1.5, 1.5

        self.zoom_factor = zoom_factor
        self.rotation_speed = rotation_speed
        self.color_iter_now=256
        self.color_iter=850
        self.min_iters=120
        self.condicion_iter=14
        # Create a colormap with 256 colors
        self.colormap_list = [ 'twilight','cividis','prism','BrBG','twilight_shifted']
        self.natural_max_iter=self.max_iter #esto es para poder ver que cambios causa esto
        self.count_zoom=1
        self.how_many_zooms=0
        self.max_zoom = 4
        self.sm=shared_memory
        self.log = Logger("Fractal", config.LOGGING_LEVEL).logging
        self.log.info(f'Constructor for {__class__.__name__}')
        self.condicion=29
        # Variables del PID
        self.error_acumulado = 0
        self.ultimo_error = 0
        self.color_map_name="inferno"
        # FPS objetivo y variables relacionadas
        self.target_fps = 22
        self.fps_actual = 0
        self.fps_history = []
        image_list=["source/imgs/"+dir for dir in os.listdir("source/imgs/") ]
        self.image_cycle = cycle(image_list)
        self.return_texture()
        self.dt = 1
        self.pid = {
            'P': 0.01,  # Proportional gain
            'I': 0.0,   # Integral gain
            'D': 0.02,  # Derivative gain
            'integral': 0.0,
            'last_error': None
        }

    def return_texture(self):
        image = next(self.image_cycle)
        self.log.info(f"image ,{image} ")
        gradient_image = cv2.imread(
            image)

        gradient_image = cv2.resize(gradient_image, (1024, 720))

        gradient_array = gradient_image.astype(np.float32) / 255.0
        gradient = gradient_array[gradient_array.shape[0] // 2, :, :3]
        self.color_array = (gradient * 255).astype(np.uint8)

    def update_pid(self, error):
        self.pid['integral'] += error * self.dt
        derivative = error - self.pid['last_error'] if self.pid['last_error'] is not None else 0.0
        derivative = derivative / self.dt
        self.pid['last_error'] = error

        P_term = self.pid['P'] * error
        I_term = self.pid['I'] * self.pid['integral']
        D_term = self.pid['D'] * derivative

        return P_term + I_term + D_term

    @staticmethod
    @cuda.jit(fastmath=True)
    def mandelbrot_kernel(min_x, max_x, min_y, max_y, image, boundary_points, iters, color_iter, color_array,condicion,condicion_iter):


        height, width, _ = image.shape
        pixel_size_x = (max_x - min_x) / width
        pixel_size_y = (max_y - min_y) / height

        startX, startY = cuda.grid(2)
        gridX = cuda.gridDim.x * cuda.blockDim.x
        gridY = cuda.gridDim.y * cuda.blockDim.y

        log2=math.log(float(2))
        len_color_array= len(color_array)
        for x in range(startX, width, gridX):
            real = min_x + x * pixel_size_x
            for y in range(startY, height, gridY):
                imag = min_y + y * pixel_size_y
                c = complex(real, imag)
                z = 0.0j

                for i in range(iters):

                    z = z * z + c

                    magnitud_squared=z.real*z.real+z.imag*z.imag
                    if  (magnitud_squared) >= 4.0:
                        if (magnitud_squared) <= condicion:
                            if i > condicion_iter:

                                color_idx = int(math.log(float(i + 1)) * color_iter) % len_color_array

                            else:


                                nu = i - math.log(math.log(float(magnitud_squared))) / log2
                                nu = nu * color_iter
                                color_idx = int(nu) % len_color_array
                        else:

                            if i > condicion_iter:
                               gradient = ((i - iters) / float(iters)) ** 4
                               color_idx = int(gradient * (len_color_array - 1)) % len_color_array

                            else:
                                color_idx = i % color_iter

                        image[y, x, 0] = color_array[color_idx, 0]
                        image[y, x, 1] = color_array[color_idx, 1]
                        image[y, x, 2] = color_array[color_idx, 2]

                        if iters - 8 <= i < iters:
                            boundary_points[y, x] = 1  # Marcar puntos de frontera
                        break
                else: # si no hay un break entonces el punto z que estamos viendo no escapa es negro

                    color_idx = int(math.log1p(magnitud_squared)* color_iter) % len_color_array  # Ejemplo usando sin()
                    image[y, x, 0] = color_array[color_idx, 0]
                    image[y, x, 1] = color_array[color_idx, 1]
                    image[y, x, 2] = color_array[color_idx, 2]


    def create_frame(self, x_min, x_max, y_min, y_max, angle):
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        boundary_points = np.zeros((self.height, self.width), dtype=np.uint8)
        d_image = cuda.to_device(image)
        d_boundary_points = cuda.to_device(boundary_points)
        d_color_array = cuda.to_device(self.color_array)

        threadsperblock = (THREADS_PER_BLOCK[0], THREADS_PER_BLOCK[0])
        blockspergrid_x = int(math.ceil(self.height / threadsperblock[0]))
        blockspergrid_y = int(math.ceil(self.width / threadsperblock[1]))
        blockspergrid = (blockspergrid_x, blockspergrid_y)

        color_iter=self.sm["color_iter"]

        self.mandelbrot_kernel[blockspergrid, threadsperblock](x_min, x_max, y_min, y_max, d_image, d_boundary_points,self.max_iter,
                                                               color_iter, d_color_array, self.condicion,self.condicion_iter)
        d_image.to_host()
        d_boundary_points.to_host()
        return image, boundary_points

    def find_nearest_boundary_point(self, x, y, boundary_points):
        nearest_point = None
        min_distance = float('inf')

        for bx in range(self.width):
            for by in range(self.height):
                if boundary_points[by, bx]:
                    distance = math.sqrt((bx - x) ** 2 + (by - y) ** 2)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_point = (bx, by)

        return nearest_point

    def draw_circles_on_boundaries(self, image, boundary_points, color=(0, 0, 255), radius=2):
        """
        Draws circles on the image at the boundary points.

        Args:
        image: The image where the circles will be drawn.
        boundary_points: An array indicating the boundary points.
        color: The color of the circles (B, G, R).
        radius: The radius of the circles.
        """
        for y in range(self.height):
            for x in range(self.width):
                if boundary_points[y, x] == 1:
                    cv2.circle(image, (x, y), radius, color, -1)  # -1 fills the circle

    def update_bounds(self):
        # if self.zoom_center_changed:
        if self.sm["zoom_center_changed"] and self.count_zoom==1:
            self.how_many_zooms = self.how_many_zooms+1

            self.max_iter=self.const_max_inters
            if self.how_many_zooms>=self.max_zoom:
                self.reset_specs()
                self.generate_frame=True
                self.sm["zoom_center_changed"] = False #esto hace que frene el zoom y no siga una vez mas
                return None
            self.sm["zoom_center_changed"] = False


            self.click_x= self.sm["click_x"]
            self.click_y= self.sm["click_y"]

            nearest_boundary_point = self.find_nearest_boundary_point(self.click_x, self.click_y, self.boundary_points)

            if nearest_boundary_point:
                self.click_x, self.click_y = nearest_boundary_point

            x_range, y_range = self.x_max - self.x_min, self.y_max - self.y_min
            new_x_center = self.x_min + (self.click_x / self.width) * x_range
            new_y_center = self.y_min + (self.click_y / self.height) * y_range

            self.x_min, self.x_max = new_x_center - x_range / 2, new_x_center + x_range / 2
            self.y_min, self.y_max = new_y_center - y_range / 2, new_y_center + y_range / 2

            self.max_iter=self.max_iter+0
            self.natural_max_iter = self.max_iter
            self.count_zoom = 60
            self.max_iter=self.max_iter/self.count_zoom
            self.iter_step=self.max_iter


        if self.count_zoom>1:


            dx, dy = (self.x_max - self.x_min) * (1 - self.zoom_factor) / 2, (self.y_max - self.y_min) * (
                        1 - self.zoom_factor) / 2
            dx =dx/self.count_zoom
            dy = dy/self.count_zoom
            self.x_min, self.x_max = self.x_min + dx, self.x_max - dx
            self.y_min, self.y_max = self.y_min + dy, self.y_max - dy
            self.max_iter = self.max_iter + self.iter_step

            self.count_zoom=self.count_zoom-1

    def setup_window(self):
        cv2.namedWindow('Fractal', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Fractal', 1920, 1080)
        cv2.setMouseCallback('Fractal', self.on_click)

    def on_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.click_x, self.click_y = x, y
            self.zoom_center_changed = True
            self.sm["zoom_center_changed"] = True
            self.sm["click_x"], self.sm["click_y"] = x, y

    def update_frame(self):
        color_iter=self.sm["color_iter"]
        condition_1 = self.color_iter_now != color_iter
        if condition_1:
            self.color_iter_now=color_iter
        condition_2 = self.count_zoom>1

        return self.sm["zoom_center_changed"] or condition_1 or condition_2
    def reset_specs(self):
        '''
        vuelve el fractal a un estado inicial
        Returns:
        '''
        self.x_min, self.x_max = -2.0, 1.0
        self.y_min, self.y_max = -1.5, 1.5
        self.max_iter = self.const_max_inters
        self.how_many_zooms=0

    def take_care_of_sending_frame(self, frame):
        self.sm['fractal_frame'] = frame

    def calculate_fps(self, show=True):

        new_frame_time = time.time()
        self.dt = new_frame_time - self.prev_frame_time
        self.fps_actual = 1 / self.dt

        self.fps_history.append(self.fps_actual)

        self.fps_history = self.fps_history[-24:]

        avg_fps = sum(self.fps_history) / len(self.fps_history)

        fps_text = f'FPS: {avg_fps:.2f}  self.max_iter {self.max_iter}'
        if show:
            cv2.putText(self.fractal_image, fps_text, (10, 70),  # Adjusted y from 30 to 50
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (100, 255, 0),
                        3, cv2.LINE_AA)


    def dibujar_cursor(self):

        cursor = self.sm['cursor_position']

        if len(cursor):
            x, y = cursor
            color = (255, 255, 255)

            cv2.circle(self.fractal_image,
                       (int((1 - x) * self.width), int(y * self.height)), 5,
                       color, -1)

    def dibujar_circunsferencia_de_escape(self):
        array_of_points = self.sm['array_of_points']
        self.cantidad_de_puntos = len(array_of_points)
        cantidad_de_colores = len(self.sm['rgb'])
        hay_nuevos_colores = self.current_cantidad_de_colores < cantidad_de_colores
        if self.cantidad_de_puntos and cantidad_de_colores:
            self.current_cantidad_de_colores = cantidad_de_colores
            position = array_of_points[-1]
            color_rgb = self.sm['rgb'][-1]

            r, g, b = int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2])

            nueva_velocidad = self.sm['note_velocity']

            if hay_nuevos_colores and nueva_velocidad:
                self.current_velocity = nueva_velocidad

            relative_radius = (0.10 + (self.current_velocity / 50))
            # Coordenadas del circulo
            circle_center_x = int((1 - position[0]) * self.width)
            circle_center_y = int(position[1] * self.height)
            circle_radius = int(relative_radius * min(self.width, self.height))

            cv2.circle(self.fractal_image, (circle_center_x, circle_center_y), circle_radius, (r, g, b), 2)

    def control(self,key):
        if key == ord('q'):
            self.sm['exit'] = True
        if key == ord('s'):
            self.return_texture()
        if key == ord('f'):
            self.generate_frame = True
        if key == ord('m'):
            self.condicion =self.condicion +1
            self.log.info(f'self.condicion {self.condicion}')
            self.generate_frame=True
        if key == ord('n'):
            self.condicion = self.condicion - 1
            self.log.info(f'self.max_iter {self.color_iter}')
            self.generate_frame=True

        if key == ord('i'):
            self.condicion_iter =self.condicion_iter +1
            self.log.info(f'self.condicion_iter {self.condicion_iter}')
            self.generate_frame=True
        if key == ord('u'):
            self.condicion_iter = self.condicion_iter - 1
            self.log.info(f'self.condicion_iter {self.condicion_iter}')
            self.generate_frame=True


        if key == ord('p'):
         self.pid['P'] +=1
         self.log.info(f'self.max_iter {self.max_iter} {self.pid}')
        if key == ord('o'):
            self.pid['P'] -= 1
            self.log.info(f'self.max_iter {self.max_iter} {self.pid}')
        if key == ord('i'):
            self.pid['I'] += 0.001
            self.log.info(f'self.max_iter {self.max_iter} {self.pid}')
        if key == ord('u'):
            self.pid['I'] -= 0.001
            self.log.info(f'self.max_iter {self.max_iter} {self.pid}')

        if key == ord('d'):
            self.pid['D'] += 0.01
            self.log.info(f'self.max_iter  {self.max_iter} {self.pid}')
        if key == ord('s'):
            self.pid['D'] -= 0.01
            self.log.info(f'self.max_iter  {self.max_iter} {self.pid}')

    def run(self):

        self.generate_frame=True
        self.fractal_image=[]
        self.color_frame= None
        self.arrows = []
        self.setup_window()
        self.current_cantidad_de_colores=0
        self.current_velocity=0.01
        self.fps_history = []
        self.cantidad_de_puntos=0
        while True:
            self.prev_frame_time = time.time()
            angle=0
            self.generate_frame = self.update_frame()
            self.update_bounds()

            # Generar fractal e identificar puntos de frontera
            if self.generate_frame:

                self.fractal_image, self.boundary_points = self.create_frame(self.x_min, self.x_max, self.y_min, self.y_max,
                                                                    angle)

                update_thread = Thread(target=self.take_care_of_sending_frame, args=(self.fractal_image,))
                update_thread.start()
                self.calculate_fps()
                self.apply_PID()

            self.dibujar_cursor()

            self.dibujar_circunsferencia_de_escape()

            if self.generate_frame or self.cantidad_de_puntos:
                cv2.imshow('Fractal', self.fractal_image)
            # # Handle user input
            key = cv2.waitKey(1) & 0xFF
            self.control(key)
            if self.sm['exit']:
                break

        self.log.info("fractal visual has finished")
        cv2.destroyAllWindows()

    def apply_PID(self):
        ###PID
        # Calcular error entre objetivo y FPS actuales
        error = self.target_fps - self.fps_actual

        pid_adjustment = self.update_pid(error)

        self.max_iter -= pid_adjustment
        self.max_iter = max(self.min_iters, min(self.max_iter, 2000))  # Ensure max_iter stays within bounds

        #
        # if avg_fps < 24 and self.max_iter >120:
        #     self.max_iter -= 1
        # if avg_fps > 24 :
        #     self.max_iter += 1
        #     # Ensure max_iter doesn't go below a certain threshold