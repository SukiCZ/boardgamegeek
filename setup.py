# coding=utf-8

from setuptools import find_packages, setup

from codecs import open

with open("README.rst", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="boardgamegeek2",
    version="1.0.1",
    packages=find_packages(),
    license="BSD",
    author="Cosmin Luță",
    author_email="q4break@gmail.com",
    description="A Python interface to boardgamegeek.com's API",
    long_description=long_description,
    url="https://github.com/lcosmin/boardgamegeek",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    install_requires=[
        "requests>=2.31.0,<3.0.0",
        "requests-cache>=1.1.1,<2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "boardgamegeek = boardgamegeek.main:main"
        ]
    }
)
