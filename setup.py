from setuptools import setup

requirements = [
    'dkpro-cassis',
    'pdfminer.six',
    'numpy'
]

setup(
    name='BIOfid Workshop Demo',
    version='1.0',
    description='Tools to use on BIOfid workshops',
    license="AGPLv3",
    long_description='',
    long_description_content_type="text/markdown",
    author='Adrian Pachzelt',
    author_email='a.pachzelt@ub.uni-frankfurt.de',
    url="https://www.biofid.de",
    download_url='https://github.com/FID-Biodiversity/workshop-demo',
    packages=['biofid_demo'],
    package_data={'biofid_demo': ['resources/*.xml']},
    include_package_data=True,
    python_requires='>=3.7',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest',
        ]
    }
)
