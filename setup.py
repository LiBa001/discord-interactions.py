from setuptools import setup, find_packages

with open("README.rst", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="discord-interactions.py",
    version="0.1.0.dev0",
    description="A library around the Discord Interactions API",
    long_description=readme,
    long_description_content_type="text/x-rst",
    url="https://github.com/LiBa001/discord-interactions.py",
    author="Linus Bartsch",
    author_email="pypi@libasoft.de",
    license="MIT",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.10",
    install_requires=["pynacl", "requests"],
    extras_require={"flask": ["flask[async]>=2.0"]},
    keywords="discord discord-py discord-bot wrapper",
    packages=find_packages(exclude=["examples", "tests", "docs"]),
    data_files=None,
)
