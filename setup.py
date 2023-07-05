# -*- coding: utf-8 -*-

import os
import setuptools


assert os.environ.get("GITHUB_REF_TYPE") == "tag"
assert os.environ.get("GITHUB_REF_NAME")
VERSION = os.environ["GITHUB_REF_NAME"]


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="kutana",
    version=VERSION,
    author="Michael Kryukov",
    author_email="kryukov.ms@ya.ru",
    keywords=[
        "asyncio",
        "library",
        "telegram",
        "vkontake",
    ],
    description="The library for developing systems for messengers and social networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ekonda/kutana",
    packages=setuptools.find_packages(),
    install_requires=["aiohttp>=3.6", "motor>=2.3", "pyyaml>=5.3"],
    entry_points={
        "console_scripts": [
            "kutana = kutana.cli:run",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
