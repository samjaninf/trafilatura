"""
Scrapes the main text of web pages while preserving some structure
https://github.com/adbar/trafilatura
"""

import re
from pathlib import Path

from setuptools import setup


def get_version(package):
    "Return package version as listed in `__version__` in `init.py`"
    initfile = Path(package, "__init__.py").read_text()  # Python >= 3.5
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", initfile)[1]


def get_long_description():
    "Return the README"
    with open("README.md", "r", encoding="utf-8") as filehandle:
        long_description = filehandle.read()
    return long_description


# some problems with installation solved this way
extras = {
    "all": [
        "brotli",
        "cchardet >= 2.1.7; python_version < '3.11'",  # build issue
        "faust-cchardet >= 2.1.19; python_version >= '3.11'",
        "htmldate[speed] >= 1.9.0",
        "py3langid >= 0.2.2",
        "pycurl >= 7.45.3",
        "urllib3[socks]",
        "zstandard >= 0.20.0",
    ],
    "gui": [
        "Gooey >= 1.0.1",
    ],
}

setup(
    name="trafilatura",
    version=get_version("trafilatura"),
    description="Python package and command-line tool designed to gather text on the Web, includes all necessary discovery and text processing components to perform web crawling, downloads, scraping, and extraction of main texts, metadata and comments.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        # As from https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        #'Development Status :: 6 - Mature',
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security",
        "Topic :: Text Editors :: Text Processing",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: Markdown",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Utilities",
    ],
    keywords=[
        "corpus",
        "html2text",
        "news-crawler",
        "natural-language-processing",
        "scraper",
        "tei-xml",
        "text-extraction",
        "webscraping",
        "web-scraping",
    ],
    url="https://trafilatura.readthedocs.io",
    project_urls={
        "Documentation": "https://trafilatura.readthedocs.io",
        "Source": "https://github.com/adbar/trafilatura",
        "Blog": "https://adrien.barbaresi.eu/blog/tag/trafilatura.html",
    },
    author="Adrien Barbaresi",
    author_email="barbaresi@bbaw.de",
    license="Apache-2.0",
    packages=["trafilatura"],
    package_data={
        "trafilatura": [
            "data/tei-schema-pickle.lzma",
            "data/jt-stopwords-pickle.lzma",
            "settings.cfg",
        ]
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "certifi",
        "charset_normalizer >= 3.2.0",
        "courlan >= 1.3.1",
        "htmldate >= 1.9.0",
        "justext >= 3.0.1",
        # see tests on Github Actions
        "lxml == 4.9.2 ; platform_system == 'Darwin' and python_version <= '3.8'",
        "lxml >= 5.2.2 ; platform_system != 'Darwin' or python_version > '3.8'",
        "urllib3 >= 1.26, < 3",
    ],
    extras_require=extras,
    entry_points={
        "console_scripts": [
            "trafilatura=trafilatura.cli:main",
            "trafilatura_gui=trafilatura.gui:main",
        ],
    },
    # platforms='any',
    tests_require=["pytest"],
    zip_safe=False,
)
