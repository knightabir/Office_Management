import inspect
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys

logger = logging.getLogger()
funcFormat = '{} {} {} '

LOG_FILE_PATH = './log/run.log'

# Ensure the log directory exists
log_directory = os.path.dirname(LOG_FILE_PATH)
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
    
logging.getLogger('pymongo').setLevel(logging.WARNING)
# Create handlers
file_handler = TimedRotatingFileHandler(
    LOG_FILE_PATH,
    when="H",
    interval=1,
)
console_handler = logging.StreamHandler()

# Configure logging
logging.basicConfig(
    format='| %(asctime)s,%(msecs).3d | %(levelname).1s | %(name)1s | %(message)s',
    datefmt='%Y:%m:%d %H:%M:%S',
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
    
)
logging.info('------')
func = inspect.currentframe().f_back.f_code
caller = inspect.getframeinfo(inspect.stack()[1][0])
func = funcFormat.format(
    os.path.relpath(func.co_filename),
    str(caller.lineno),
    func.co_name,
)
logging.info(func + 'All Logs written in {}'.format(LOG_FILE_PATH))


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        temp_linebuf = self.linebuf + buf
        self.linebuf = ''
        for line in temp_linebuf.splitlines(True):
            if line[-1] == '\n':
                self.logger.log(self.log_level, line.rstrip())
            else:
                self.linebuf += line

    def flush(self):
        if self.linebuf != '':
            self.logger.log(self.log_level, self.linebuf.rstrip())
        self.linebuf = ''


stdout_logger = logging.getLogger('STDOUT')
sl = StreamToLogger(stdout_logger, logging.INFO)
sys.stdout = sl

stderr_logger = logging.getLogger('STDERR')
sl = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl


class Log:
    # For Information py_log
    @staticmethod
    def i(tag='', message=''):
        func = inspect.currentframe().f_back.f_code
        caller = inspect.getframeinfo(inspect.stack()[1][0])
        func = funcFormat.format(
            os.path.relpath(func.co_filename),
            caller.lineno,
            func.co_name,
        )
        logger.info(func + str(tag) + '\t' + str(message))

    # For error py_log
    @staticmethod
    def e(tag='', message=''):
        func = inspect.currentframe().f_back.f_code
        caller = inspect.getframeinfo(inspect.stack()[1][0])
        func = funcFormat.format(
            os.path.relpath(func.co_filename),
            caller.lineno,
            func.co_name,
        )
        logger.error(func + str(tag) + '\t' + str(message))

    # For debug py_log
    @staticmethod
    def d(tag='', message=''):
        func = inspect.currentframe().f_back.f_code
        caller = inspect.getframeinfo(inspect.stack()[1][0])
        func = funcFormat.format(
            os.path.relpath(func.co_filename),
            caller.lineno,
            func.co_name,
        )
        logger.debug(func + str(tag) + '\t' + str(message))

    # For warning py_log
    @staticmethod
    def w(tag='', message=''):
        func = inspect.currentframe().f_back.f_code
        caller = inspect.getframeinfo(inspect.stack()[1][0])
        func = funcFormat.format(
            os.path.relpath(func.co_filename),
            caller.lineno,
            func.co_name,
        )
        logger.warning(func + str(tag) + '\t' + str(message))

    # Showing critical py_log
    @staticmethod
    def c(tag='', message=''):
        func = inspect.currentframe().f_back.f_code
        caller = inspect.getframeinfo(inspect.stack()[1][0])
        func = funcFormat.format(
            os.path.relpath(func.co_filename),
            caller.lineno,
            func.co_name,
        )
        logger.critical(func + str(tag) + '\t' + str(message))
