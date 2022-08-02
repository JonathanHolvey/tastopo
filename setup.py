from setuptools import setup, find_packages
from os import path
import re

here = path.abspath(path.dirname(__file__))
content_url = 'https://raw.githubusercontent.com/jonathanholvey/tastopo/main'
url_regex = r'(?<=\()\./([^)]+)'


def abs_urls(markdown):
    """Substitute relative URLs in Markdown with absolute repo URLs"""
    return re.sub(url_regex, f'{content_url}/\\1', markdown)


with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='tastopo',
    version='1.1.1',
    description='Generate printable topographic maps for anywhere in Tasmania',
    long_description=abs_urls(long_description),
    long_description_content_type='text/markdown',
    url='https://github.com/jonathanholvey/tastopo',
    author='Jonathan Holvey',
    author_email='jonathan.holvey@outlook.com',
    project_urls={
        'Bug Reports': 'https://github.com/jonathanholvey/tastopo/issues',
        'Source': 'https://github.com/jonathanholvey/tastopo/',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'Topic :: Other/Nonlisted Topic',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages("./src"),
    package_dir={'': './src'},
    package_data={'': ['templates/default.svg']},
    python_requires='>=3.6, <4',
    # This is generated automatically. Run `pipenv run setup-sync` to update
    install_requires=[
        'docopt~=0.6',
        'requests~=2.26',
        'svglib~=1.1',
        'reportlab~=3.5',
        'pillow~=8.3',
    ],

    scripts=['./tastopo'],
)
