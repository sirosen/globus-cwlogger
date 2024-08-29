from setuptools import find_packages, setup

setup(
    name="globus_cw_client",
    version="24.1",
    packages=find_packages(),
    # descriptive info, non-critical
    description="Client for Globus CloudWatch Logger",
    url="https://github.com/globus/globus-cwlogger",
    install_requires=[
        "orjson",
    ],
)
