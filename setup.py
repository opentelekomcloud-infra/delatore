from os import path

from setuptools import find_packages, setup

version = '0.4.8.dev3'

cur_dir = path.abspath(path.dirname(__file__))
with open(path.join(cur_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='delatore',
    version=version,
    description='Monitoring of customer service monitoring',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/opentelekomcloud-infra/delatore',
    license='Apache-2.0',
    author='OTC team',
    packages=find_packages(),
    package_data={'delatore.configuration.resources': ['*.yaml']},
    classifiers=[
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    platforms=['any'],
    python_requires='>=3.7'
)
