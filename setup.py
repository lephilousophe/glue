

import sys

from setuptools import setup, find_packages

install_requires=[
    'Pillow>=2.2.2',
    'Jinja2>=2.7,<2.10',
]

tests_require=[
    'cssutils>=0.9.10,<1.0',
]

setup(
    name='glue',
    version='0.13',
    url='http://github.com/jorgebastida/glue',
    license='BSD',
    author='Jorge Bastida',
    author_email='me@jorgebastida.com',
    description='Glue is a simple command line tool to generate sprites.',
    long_description=('Glue is a simple command line tool to generate '
                      'sprites using any kind of source images like '
                      'PNG, JPEG or GIF. Glue will generate a unique PNG '
                      'file containing every source image and a map file '
                      'including the necessary information to use it.'),
    keywords = "glue sprites css cocos2d",
    packages = find_packages(),
    platforms='any',
    python_requires='>=3.7',
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Utilities'
    ],
    entry_points = {
        'console_scripts': [
            'glue = glue.bin:main',
        ]
    },
    zip_safe = False,
)
