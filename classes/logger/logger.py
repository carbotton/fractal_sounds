import logging


class Logger():
    def __init__(self, name=None, log_level=logging.DEBUG):
        # create a logger with the given name
        self.logging: logging.Logger = logging.getLogger(name)
        # log all messages, debug and up
        self.logging.setLevel(log_level)

        # remove all handlers if there are any
        for handler in self.logging.handlers[:]:
            self.logging.removeHandler(handler)

        # create a handler
        ch = logging.StreamHandler()
        # set level for handler
        ch.setLevel(log_level)
        # create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # set formatter for handler
        ch.setFormatter(formatter)
        # add handler to logger
        self.logging.addHandler(ch)
