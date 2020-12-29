from setuptools import setup, find_packages

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='discord-interactions-wrapper',
    version='0.0.1',
    description='A wrapper for the Discord Interactions API',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/LiBa001/discord-interactions-wrapper',
    author='Linus Bartsch',
    author_email='pypi@libasoft.de',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8'
    ],
    python_requires='>=3.8',
    install_requires=['discord.py >=1,<2'],
    keywords='discord discord-py discord-bot wrapper',
    packages=find_packages(exclude=["examples"]),
    data_files=None
)
