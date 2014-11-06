import os
from setuptools import setup, find_packages

long_description = (open('README.rst').read())

exec(open('friendly/silverpop/version.py').read())
setup(name='friendly-silverpop',
      version='0.1.0',
      url = 'http://butfriendly.com',
      description = 'Silverpop Engage API client',
      author = 'Christian Schmitz',
      author_email = 'chris@butfriendly.com',
      long_description = long_description,
      classifiers = [
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Topic :: Software Development :: Testing',
          'Topic :: Internet :: WWW/HTTP',
      ],
      packages = find_packages(exclude=['tests']),
      namespace_packages = ['friendly',],
      install_requires = [
          'requests',
          'python-dateutil',
      ],
)