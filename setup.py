import setuptools




with open('README.rst', 'r') as f:
    description = f.read()

setuptools.setup(
    name='my-django',
    version='0.0.1',
    author='C. Bryant Glisson',
    author_email="contact@gfg.com",
    packages=['my_django'],
    description='A library of helpful tools for javascript and Django',
    long_description=description,
    long_description_content_type='text/markdown',
    url='https://github.com/songofchrist/my-django',
    license='MIT',
    python_requires='>=3.9',
    install_requires=[]
)
