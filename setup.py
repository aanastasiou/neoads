import sys

from setuptools import setup, find_packages

setup(
    name="neoads",
    version="0.0.3",
    description="Abstract Data Structures (Set, Map, Doubly Linked List) over the neo4j graph database.",
    long_description=open("README.rst").read(),
    author="Athanasios Anastasiou",
    author_email="athanastasiou@gmail.com",
    zip_safe=True,
    url="",
    license="",
    packages=find_packages(exclude=("test", "test.*")),
    keywords="graph neo4j ORM OGM ADS Data Structure Modelling",
    setup_requires=["pytest-runner"] if any(x in ("pytest", "test") for x in sys.argv) else [],
    tests_require=["pytest"],
    install_requires=['neomodel'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Topic :: Database",
    ])
