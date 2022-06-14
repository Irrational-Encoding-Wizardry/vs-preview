#!/usr/bin/env python3
# coding: utf-8

import os

from setuptools import find_packages, setup

with open("README.md") as fh:
    long_description = fh.read()

with open("requirements.txt") as fh:
    install_requires = fh.read()


name = "vspreview"
version = "0.2.5"
file_name = os.path.basename(__file__)


setup(
    name=name,
    version=version,
    author="Endilll",
    maintainer='Setsugennoao',
    maintainer_email='setsugen@setsugen.dev',
    description="Preview for VapourSynth scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Irrational-Encoding-Wizardry/vs-preview",
    packages=find_packages('.', ("docs", "stubs")),
    install_requires=install_requires,
    python_requires=">=3.9",
    zip_safe=False,
    project_urls={
        'Documentation': 'https://github.com/Irrational-Encoding-Wizardry/vs-preview/#readme',
        'Source': 'https://github.com/Irrational-Encoding-Wizardry/vs-preview',
        'Tracker': 'https://github.com/Irrational-Encoding-Wizardry/vs-preview/issues'
    },
    classifiers=[
        "Topic :: Multimedia :: Graphics",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'vspreview = vspreview.init:main'
        ]
    },
    command_options={
        "build_sphinx": {
            "project": (file_name, name),
            "version": (file_name, version),
            "release": (file_name, version),
            "source_dir": (file_name, "docs")
        }
    }
)
