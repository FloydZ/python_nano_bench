#!/usr/bin/env python3
"""installation script """
import os
import sys
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info


setup(
    name='python_nano_bench',
    version='0.0.1',
    author='Floyd Zweydinger',
    author_email='zweydfg8+github@rub.de',
    description='TODO',
    long_description="TODO",
    long_description_content_type='text/markdown',
    install_requires=["setuptools", ],
    cmdclass={
        'install': install,
        'develop': develop,
        'egg_info': egg_info,
    },
    #package_data={'': ['./']},
    #requires=[],
    project_urls={
        'Source Code': 'https://github.com/FloydZ/python_nano_bench',
        "Author's Website": 'https://pingfloyd.de',
        'Documentation': '',
    },
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
        'Topic :: Utilities',
    ],
)
