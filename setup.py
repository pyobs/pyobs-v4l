from setuptools import setup

setup(
    name='pyobs-v4l',
    version='0.9',
    author='Tim-Oliver Husser',
    author_email='thusser@uni-goettingen.de',
    description='pyobs module for Video4Linux cameras',
    packages=['pyobs_v4l'],
    install_requires=[line.strip() for line in open("requirements.txt").readlines()]
)
