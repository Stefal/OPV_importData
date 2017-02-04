#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='importData',
    packages=find_packages(),
    author="",
    author_email="",
    description="The import script of OPV",
    long_description=open('README.md').read(),
    # install_requires= ,
    # Active la prise en compte du fichier MANIFEST.in
    include_package_data=True,
    url='https://github.com/OpenPathView/batchPanoMaker',
    entry_points={
        'console_scripts': [
            'opv-import = importData.__main__:main',
        ],
    }
)
