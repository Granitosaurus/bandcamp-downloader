from distutils.core import setup

setup(
    name='bandcamp-downloader',
    version='1.0',
    packages=['bandcampdl'],
    url='',
    license='GPLv3',
    author='granitosaurus',
    install_requires=[
        'click',
        'requests',
        'parsel',
    ],
    entry_points="""
        [console_scripts]
        bandcamp-dl=bandcampdl.downloader:cli
    """,
    author_email='bernardas.alisauskas@gmail.com',
    description='Simple cli downloader for bandcamp albums'
)
