"""Implements a process wrapper for a minecraft server"""

__author__ = 'rmanders'

import logging
import time
import select
import Queue
import signal
import threading
import fcntl
import daemon
import io
import sys
import os
from subprocess import Popen, PIPE, STDOUT
from mcutils import InputStreamChunker, eula_agree
from logging.handlers import RotatingFileHandler

# Default argument values
DEF_JVM_PATH = ''
DEF_MC_JAR = '/Users/rmanders/Documents/Development/rmanders/github/Python-Minecraft-Wrapper/pmw/minecraft.jar'
DEF_SERVER_PATH = './'
DEF_JVM_ARGS = '-Xms1024M -Xmx1024M'
DEF_MC_ARGS = 'nogui'
DEF_SERVER_IO = "./pmw.txt"
DEF_DAEMONIZE = False
DEF_TIMEOUT = 500 #MILLISECONDS
DEF_CWD = "/tmp"

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def get_output(queue):
    outLines = []
    try:
        while True:
            outLines.append(queue.get_nowait())
    except Queue.Empty:
        return outLines

def set_non_blocking_fd(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


class ServerIoType:
    HEADLESS = 0
    CONSOLE = 1
    WEB = 2
    IRC = 3

    def __init__(self):
        pass


class MinecraftServerWrapper (object):

    def __init__(self, **kwargs):

        self.jvm_path = kwargs.get('jvm_path', DEF_JVM_PATH)
        self.mc_jar_path = kwargs.get('mc_jar_path', DEF_MC_JAR)
        self.server_path = kwargs.get('server_path', DEF_SERVER_PATH)
        self.jvm_args = kwargs.get('jvm_args', DEF_JVM_ARGS)
        self.mc_args = kwargs.get('mc_args', DEF_MC_ARGS)
        self.daemonize = kwargs.get('daemonize', DEF_DAEMONIZE)
        self.timeout = kwargs.get('timeout', DEF_TIMEOUT)
        self.cwd = kwargs.get('cwd', DEF_CWD)
        self.log = None
        self.mc_log = None
        self.mc_process = None
        self.charbuff = ""

    def _init_logging(self):
        """Sets up logging for the application"""

        # Set up application logging
        self.log = logging.getLogger(__name__)
        rfh1 = RotatingFileHandler(self.cwd + "/pmw_app.log", mode="a", maxBytes=1000000, backupCount=3, encoding=None)
        rfh1.setLevel(logging.DEBUG)
        fmt1 = logging.Formatter(fmt="[%(asctime)s][%(levelname)s] - %(message)s")
        rfh1.setFormatter(fmt1)
        self.log.addHandler(rfh1)
        self.log.setLevel(logging.DEBUG)

        # Set up minecraft server output log
        self.mc_log = logging.getLogger("minecraft-server")
        rfh2 = RotatingFileHandler(self.cwd + "/minecraft-server.log", mode="a", maxBytes=1000000, backupCount=3)
        fmt2  = logging.Formatter(fmt="%(message)s")
        rfh2.setLevel(logging.DEBUG)
        rfh2.setFormatter(fmt2)
        self.mc_log.addHandler(rfh2)
        self.mc_log.setLevel(logging.DEBUG)


    def build_server_commands(self):
        """Returns a list representing the command to start the minecraft server using Popen"""
        return [
            self.jvm_path + 'java'] + \
            self.jvm_args.split(' ') + \
            ['-jar',
            self.mc_jar_path,
            self.mc_args
        ]

    def readchars(self, fileObject):
        """Reads one character at a time"""
        while len(select.select([fileObject],[],[],self.timeout)[0]) > 0:
            ch = fileObject.read(1)
            if ch == '\n':
                self.log.info("OUTPUT: %s" % self.charbuff.strip())
                self.charbuff = ""
            if ch is not None:
                self.charbuff = self.charbuff + ch


    def run(self):

        # Set up logging
        self._init_logging()
        #keep_fds = [fh.stream.fileno()]

        eula_agree(self.cwd, True)

        # Start the Server Process
        cmd = self.build_server_commands()
        self.log.info("Starting server with command: \n\t%s" % ' '.join(cmd))
        try:
            self.mc_process = Popen(cmd, bufsize=1, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=self.cwd, universal_newlines=True)
        except Exception as ex:
            self.log.exception("Exception while start subprocess!")
            return

        # Set up the output queues
        self.log.debug("Starting output reader thread")
        outQueue = Queue.Queue()
        outQueueThread = threading.Thread(target=enqueue_output, args=(self.mc_process.stdout, outQueue))
        outQueueThread.daemon = True
        outQueueThread.start()

        # Set up termination signal handlers
        def signal_handler(signal, frame):
            self.log.debug("SIGNAL (%s) received" % str(signal))
            if self.mc_process is not None:
                self.mc_process.terminate()
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run loop for process
        self.log.debug("Entering Run Loop")
        while True:
            #self.log.debug("Run Loop Iteration..")
            if self.mc_process is None:
                self.log.error("Process did not start (was null). Exiting")
                break;
            if self.mc_process.poll() is not None:
                self.log.info("Minecraft Server Exited with status: %s" % str(self.mc_process.returncode))
                self.log.info("POLL RESULT: " + str(self.mc_process.poll()))
                #self.readchars(self.mc_process.stdout)
                #self.log.info("OUTPUT: %s" % str(self.mc_process.stdout.readlines()))
                break;
            #self.log.info("HERE 1......")
            #self.log.info("OUTPUT: %s" % str(self.mc_process.stdout.readline()))
            #self.readchars(self.mc_process.stdout)
            lines = get_output(outQueue)
            if len(lines) > 0:
                for line in lines:
                    self.mc_log.info("OUTPUT: %s" % str(line.strip()))
            time.sleep(0.5)
        self.log.info("Exited process run loop")



if __name__ == '__main__':

    server = MinecraftServerWrapper(daemonize=True)
    #server.run()
    with daemon.DaemonContext():
        server.run()
