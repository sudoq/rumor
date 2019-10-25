import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rumorctl",
    version="1.0.0",
    description="AMQP client library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SudoQ/rumor",
    packages=setuptools.find_packages(),
    install_requires=[
        'click>=7.0,<8',
        'requests>=2.22.0,<3.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'amqpclient=amqpclient.cli:cli'
        ]
    }
)
