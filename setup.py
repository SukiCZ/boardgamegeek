from codecs import open

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="bgg-api",
    version="1.1.3",
    packages=find_packages(),
    license="BSD",
    author="Jakub Boukal",
    author_email="www.bagr@gmail.com",
    description="A Python API for boardgamegeek.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SukiCZ/boardgamegeek",
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
    entry_points={"console_scripts": ["boardgamegeek = boardgamegeek.main:main"]},
)
