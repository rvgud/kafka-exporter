import logging
class CustomJSONFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        """
        Format the timestamp as desired (e.g., "2023-09-08T08:26:08.861Z").
        """
        timestamp = super(CustomJSONFormatter, self).formatTime(record, datefmt)
        return f"{timestamp.replace(' ', 'T').replace(',', '.')}Z"
class Logger:
    def setup_logger(self,name,level):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Configure JSON formatter
        json_formatter = CustomJSONFormatter('{"@timestamp": "%(asctime)s", "message": "%(message)s", "process": "%(process)s" ,"service": "%(name)s", "filename": "%(module)s","funcName":"%(funcName)s", "severity": "%(levelname)s"}')

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(json_formatter)
        logger.addHandler(stream_handler)
        logger.propagate = False

        return logger