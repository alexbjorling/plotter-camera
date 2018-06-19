from setuptools import setup, find_packages

setup(
    name = "Plotter Library",
    version = "0.1a0",
    packages = find_packages(),
    install_requires = ['numpy'],
    include_package_data=True,
    )
