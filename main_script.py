# main_script.py

from classes.shared_memory.shared_memory import SharedMemory
from script import player_main, interpreter_main, fractal_main, fractal_player_main
from multiprocessing import Process
import win32api, win32process, win32con
from multiprocessing import freeze_support

def adjust_process_priority(pid, priority_class):
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetPriorityClass(handle, priority_class)
    win32api.CloseHandle(handle)

def main():
    shared_memory = SharedMemory().shared_memory
    interpreter_process = Process(target=interpreter_main, args=[shared_memory])
    fractal_process = Process(target=fractal_main, args=[shared_memory])
    player_process = Process(target=player_main, args=[shared_memory])
    fractal_player = Process(target=fractal_player_main, args=[shared_memory])

    interpreter_process.start()
    adjust_process_priority(interpreter_process.pid, win32process.HIGH_PRIORITY_CLASS)
    fractal_process.start()
    adjust_process_priority(fractal_process.pid, win32process.HIGH_PRIORITY_CLASS)
    player_process.start()
    fractal_player.start()

    interpreter_process.join()
    fractal_process.join()
    player_process.join()
    fractal_player.join()

if __name__ == '__main__':
    freeze_support()
    main()