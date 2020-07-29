from os import path

from setuptools import find_packages, setup

version = '0.4.7.dev1'

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='delatore',
    version=version,
    description='Monitoring of customer service monitoring',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/opentelekomcloud-infra/delatore',
    license='Apache-2.0',
    author='Anton Kachurin, Anton Sidelnikov',
    author_email='katchuring@gmail.com, email@email.com',
    packages=find_packages(),
    package_data={"delatore.configuration.resources": ["*.yaml"]},
    classifier=[
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.7'
)
