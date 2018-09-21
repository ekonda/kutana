# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Michael Krukov
:license: MIT, see LICENSE for more details.
"""

from setuptools.command.install import install
import setuptools
import os
import sys


VERSION = "0.5.0"


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version."""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('TRAVIS_TAG')

        if tag != "v" + VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )

            sys.exit(info)


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="kutana",
    version=VERSION,
    author="Michael Krukov",
    author_email="krukov.michael@ya.ru",
    keywords="engine social-networks messengers bots asyncio",
    description="The engine for developing bots for soc. networks, instant messengers and other systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vk-brain/kutana",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests==2.19",
        "aiohttp==3.3"
    ],
    python_requires='>=3.5',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
