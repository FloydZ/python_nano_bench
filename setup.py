#!/usr/bin/env python3
"""installation script """
import os
import sys
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info


def read_text_file(path):
    """ read a test file and returns its content"""
    with open(os.path.join(os.path.dirname(__file__), path)) as file:
        return file.read()

def custom_command():
    """ build the needed `AssemblyLine` package """
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
    name='python_nano_bench',
    version='0.0.1',
    author='Floyd Zweydinger',
    author_email='zweydfg8+github@rub.de',
    description='Wrapper around NanoBench',
    long_description="Python wrapper around NanoBench",
    project_urls={
        'Source Code': 'https://github.com/FloydZ/python_nano_bench',
        "Author's Website": 'https://pingfloyd.de',
        'Documentation': '',
    },
    install_requires=["setuptools", ],
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
        'egg_info': CustomEggInfoCommand,
    },
    package_dir= {'': 'python_nano_bench'},
    requires=[],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 1 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Utilities',
    ],
)
