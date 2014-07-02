#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages

def get_version():
    INIT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                           'drums', '__init__.py'))
    f = open(INIT, 'r')
    try:
        for line in f:
            if line.startswith('__version__'):
                ret = eval(line.strip().split(' = ')[1])
                assert ret.count('.') == 2, ret
                for num in ret.split('.'):
                    assert num.isdigit(), ret
                return ret
        else:
            raise ValueError("couldn't find version string")
    finally:
        f.close()

VERSION = get_version()

setup(
    name='drums',
    version=VERSION,
    author='Mani Monajjemi',
    author_email='mmonajje@sfu.ca',
    packages=find_packages(exclude=['test']),
    url='http://autonomylab.org/drums/',
    download_url = 'https://github.com/drums-project/drums-core/tarball/' + VERSION,
    license='Apache License 2.0',
    install_requires=['pcapy == 0.10.8', 'psutil >= 2.0', 'setproctitle'],
    dependency_links = ['https://github.com/CoreSecurity/pcapy/archive/0.10.8.tar.gz#egg=pcapy-0.10.8'],
    description='drums-core is a system monitoring library. It provides an easy to use async API to register system monitoring tasks.',
    test_suite='test.test_drums.get_suite'
)
