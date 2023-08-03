import setuptools




with open('README.rst', 'r') as f:
    description = f.read()

setuptools.setup(
    name='djangoat',
    version='0.0.1',
    author='Bryant Glisson',
    author_email='',
    packages=['djangoat'],
    description='A library of helpful tools for javascript and Django',
    long_description=description,
    long_description_content_type='text/markdown',
    url='https://github.com/songofchrist/djangoat',
    license='MIT',
    python_requires='>=3.9',
    install_requires=[]
)
