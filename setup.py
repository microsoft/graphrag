from setuptools import setup, find_packages

setup(
    name='graphrag',  
    version='0.3.1',  
    author='Hu Lei',
    author_email='hulei@shiyanjia.com',
    url='https://github.com/SliverBulle/graphrag_0822',
    description='add dimensions in graphrag',  
    long_description=open('README.md').read(), 
    long_description_content_type='text/markdown',  
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    packages=find_packages(exclude=['tests']),  
    install_requires=[
        'numpy',   # An example dependency
        # ... other dependencies
    ],  
)
