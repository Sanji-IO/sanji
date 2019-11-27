from setuptools import setup
import os


def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()


setup(
    name="sanji",
    version="1.1.1",
    description="Sanji Framework SDK",
    long_description=read('README.rst'),
    url="https://github.com/Sanji-IO/sanji",
    author="Sanji Team",
    author_email="sanji@moxa.com",
    license="MIT",
    packages=["sanji", "sanji.connection", "sanji.model"],
    install_requires=[
        "paho-mqtt==1.5.0",
        "simplejson==3.17.0",
        "six==1.13.0",
        "voluptuous==0.11.5"
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
