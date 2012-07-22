'''
Installer for swiftmess.

Developer cheat sheet
---------------------

Create the installer archive::

  $ python setup.py sdist --formats=zip

Upload release to PyPI::

  $ pep8 -r --ignore=E501 *.py test/*.py
  $ python test/test_swiftmess.py
  $ python setup.py sdist --formats=zip upload

Tag a release::

  $ git tag -a -m 'Tagged version 0.x.' v0.x
  $ git push --tags
'''
# Copyright (c) 2012, Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from setuptools import setup

import swiftmess

setup(
    name='swiftmess',
    version=swiftmess.__version__,
    py_modules=['swiftmess'],
    description='parse SWIFT messages for financial transactions',
    keywords='swift bank banking financial message',
    author='Thomas Aglassinger',
    author_email='roskakori@users.sourceforge.net',
    url='http://pypi.python.org/pypi/swiftmess/',
    long_description=swiftmess.__doc__,  # @UndefinedVariable
    install_requires=['setuptools'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business :: Financial',
        'Topic :: Text Processing'
    ]
)
