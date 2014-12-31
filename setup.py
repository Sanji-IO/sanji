from setuptools import setup
import sanji

setup(name="sanji",
      version=sanji.__version__,
      description="Sanji SDK",
      url="https://github.com/Sanji-IO",
      author="Sanji Team",
      author_email="sanji@moxa.com",
      license="MIT",
      packages=["sanji", "sanji.connection"],
      install_requires=["voluptuous"]
      )
