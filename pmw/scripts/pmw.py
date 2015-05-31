#!/usr/bin/env python

import os
import daemon
from ..mcutils import *
from ..mcserver2 import MinecraftServerWrapper

def main():
    cwd = os.getcwd()
    exedir = os.path.dirname(os.path.realpath(__file__))

    # Download Minecraft
    download_minecraft_server(dir=cwd)
    mc = MinecraftServerWrapper(cwd=cwd, mc_jar_path=cwd + "/minecraft-server.jar")
    eula_agree(cwd, True)
    print("Starting...")

    with daemon.DaemonContext():
        mc.run()








