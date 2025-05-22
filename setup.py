#!/usr/bin/env python3
""" setup file """

import os
import sys
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info


def custom_command():
    """ build the needed `python_nano_bench` package """
    if sys.platform in ['linux']:
        os.system('./build.sh')


class CustomInstallCommand(install):
    """ install script """
    def run(self):
        custom_command()
        install.run(self)


class CustomDevelopCommand(develop):
    """ develop script """
    def run(self):
        custom_command()
        develop.run(self)


class CustomEggInfoCommand(egg_info):
    """ custom script """
    def run(self):
        custom_command()
        egg_info.run(self)

setup(
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
        'egg_info': CustomEggInfoCommand,
    },
)
