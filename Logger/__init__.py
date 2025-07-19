from .Logger import Logger
import logging
import os
loglevel= os.environ.get('LOG_LEVEL', 'ERROR')
setlevel=logging.INFO
if(loglevel=="ERROR"):
    setlevel=logging.ERROR
elif(loglevel=="DEBUG"):
    setlevel=logging.DEBUG
global_logger = Logger().setup_logger("kafka-exporter",setlevel)