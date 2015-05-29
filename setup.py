"""Setup tools setup module"""

from setuptools import setup, find_packages

setup (

    name = "Python Minecraft Wrapper",

    version = "0.0.1",

    description = "A python wrapper to execute and control the Minecraft server jar",

    url = "https://github.com/rmanders/Python-Minecraft-Wrapper",

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.7'
    ],

    keywords = 'minecraft python wrapper',

    packages = find_packages(exclude=['venv']),

    install_requires = ['daemonize'],

    entry_points = {
        'console_scripts' : [
            #'quickrun=quickrun:main'
        ]
    }

)