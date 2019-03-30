#!/usr/bin/env python
from setuptools import setup, find_packages
from os.path import join


MODULE_NAME = 'businessplayground'
MODULE_NAME_IMPORT = MODULE_NAME  # this is how this module is imported in Python (name of the folder inside `src`)
REPO_NAME = 'businessplayground'  # repository name

VERSION = open(join('src', MODULE_NAME_IMPORT, 'resources', 'VERSION')).read().strip()


def requirements_from_pip():
    with open('requirements.txt', 'r') as pip:
        return [l.strip() for l in pip if not l.startswith('#') and l.strip()]


setup(name=MODULE_NAME,
      url='https://github.com/matheusfacure/{:s}'.format(REPO_NAME),
      author="Matheus Facure",
      package_dir={'': 'src'},
      packages=find_packages('src'),
      version=VERSION,
      install_requires=requirements_from_pip(),
      include_package_data=True,
      zip_safe=False)
