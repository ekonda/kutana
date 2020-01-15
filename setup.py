# -*- coding: utf-8 -*-

"""
:copyright: (c) 2019 by Michael Krukov
:license: MIT, see LICENSE for more details.
"""

import setuptools


VERSION = "4.1.0"


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="kutana",
    version=VERSION,
    author="Michael Krukov",
    author_email="krukov.michael@ya.ru",
    keywords=["library", "social-networks", "messengers", "bots", "asyncio"],
    description="The library for developing systems for messengers and social networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ekonda/kutana",
    packages=setuptools.find_packages(),
    install_requires=[
        "sortedcontainers>=2.1.0",
        "aiohttp>=3.6.1"
    ],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
