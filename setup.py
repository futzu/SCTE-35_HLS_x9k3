#!/usr/bin/env python3

import setuptools
import x9k3

with open("README.md", "r") as fh:
    readme = fh.read()

setuptools.setup(
    name="x9k3",
    version=x9k3.version(),
    author="Brought to you by the fine folks at fu-corp",
    author_email="spam@iodisco.com",
    description="A SCTE-35 Aware HLS Segmenter",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/futzu/x9k3",
    py_modules=["x9k3"],
    scripts=["bin/x9k3"],
    platforms="all",
    install_requires=[
        "threefive >= 2.3.69",
        "new_reader >= 0.1.3",
        "iframes >= 0.0.5",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.6",
)
