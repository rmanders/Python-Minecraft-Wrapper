"""Implements a process wrapper for a minecraft server"""

__author__ = 'rmanders'

import logging
import time
import io
import sys
from subprocess import Popen, PIPE

DEF_JVM_PATH = ''
DEF_MC_JAR = 'minecraft.jar'
DEF_SERVER_PATH = './'
DEF_JVM_ARGS = '-Xms1024M -Xmx1024M'
DEF_MC_ARGS = 'nogui'
DEF_SERVER_IO = "./pmw.txt"


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
        self.log = logging.getLogger(__name__)
        self.mc_process = None

    def build_server_commands(self):
        """Returns a list representing the command to start the minecraft server using Popen"""
        return [
            self.jvm_path + 'java'] + \
            self.jvm_args.split(' ') + \
            ['-jar',
            self.mc_jar_path,
            self.mc_args
        ]

    def start(self):
        """starts the minecraft server"""

        cmd = self.build_server_commands()
        print("Starting server with command: \n\t%s" % ' '.join(cmd))
        with io.open(DEF_SERVER_IO, 'w') as writer, io.open(DEF_SERVER_IO, 'r', 1) as reader:
            self.mc_process = Popen(cmd,
                                    bufsize=1,
                                    stdin=sys.stdin,
                                    stdout=writer,
                                    stderr=writer
            )
            while True:
                if self.mc_process is None:
                    print("Minecraft server process was empty")
                    break
                if self.mc_process.poll() is not None:
                    print("Minecraft server terminated with return code: %s" % str(self.mc_process.returncode))
                    sys.stdout.write(reader.read())
                    break

                # Write output of server to stdout (for now)
                sys.stdout.write(reader.read())

                time.sleep(0.5)


if __name__ == '__main__':

    server = MinecraftServerWrapper()
    server.start()
