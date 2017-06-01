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
    dependency_links=[
        "git+https://github.com/OpenPathView/OPV_DBRest-client.git#egg=opv_api_client-0.2",
        "git+https://github.com/OpenPathView/DirectoryManagerClient.git#egg=opv_directorymanagerclient-0.1"
    ],
    install_requires=[
        "docopt",
        "ExifRead",
        "path.py",
        "pyudev",
        "geojson",
        "opv_api_client",
        "opv_directorymanagerclient"
    ],
    # Active la prise en compte du fichier MANIFEST.in
    include_package_data=True,
    url='https://github.com/OpenPathView/OPV_importData',
    entry_points={
        'console_scripts': [
            'opv-import = importData.__main__:main',
            'opv-clean-sd = importData.cleanSD:main',
        ],
    }
)
