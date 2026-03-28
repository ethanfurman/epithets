try:
    import setuptools
    setuptools
except ImportError:
    pass
from distutils.core import setup

long_desc="""
Text user interface built on top of curses.

Installation:  `pip install epithets`
"""

py2_only = ()
py3_only = ()
make = []

data = dict(
        name='epithets',
        version='0.0.1',
        license='BSD License',
        description='Text user interface built on top of curses.',
        long_description=long_desc,
        url='https://github.com/ethanfurman/epithets',
        packages=['epithets', ],
        package_data={
           'epithets' : [
               'LICENSE',
               'README.md',
               ]
           },
        provides=['epithets'],
        install_requires=['aenum'],
        author='Ethan Furman',
        author_email='ethan@stoneleaf.us',
        classifiers=[
            'Development Status :: 2 Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Environment :: Console :: Curses',
            'Topic :: Terminals',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            'Programming Language :: Python :: 3.13',
            ],
        )

if __name__ == '__main__':
    setup(**data)
