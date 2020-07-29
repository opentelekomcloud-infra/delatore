from setuptools import find_packages, setup

version = '0.4.7'

setup(
    name='delatore',
    version=version,
    description='Monitoring of customer service monitoring',
    url='https://github.com/opentelekomcloud-infra/delatore',
    license='Apache-2.0',
    author='Anton Kachurin, Anton Sidelnikov',
    author_email='katchuring@gmail.com, email@email.com',
    packages=find_packages(),
    package_data={"delatore.configuration.resources": ["*.yaml"]},
)
