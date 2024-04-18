from setuptools import setup, find_packages
from codecs import open
from os import path, system

HERE = path.abspath(path.dirname(__file__))

# Going to setup prisma migration script here later on

setup(
    name="SolanaWebhookServer",
    version="0.1.0",
    description="A webhook server for Solana",
    author="Zayd Alzein",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=["fastapi", "uvicorn", "python-dotenv", "colorama", "prisma"],
    test_requires=["pytest", "fastapi"],
    python_requires=">=3.9.0",
    test_suite="tests"
)