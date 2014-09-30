from distutils.core import setup

setup(name='rpudb',
    version='0.0.3',
    license='MIT',
    author='Marcelo Salhab Brogliato',
    author_email='msbrogli@vialink.com.br',
    description='Remote pudb',
    long_description=open('README.md').read(),
    packages=['rpudb'],
    url='https://github.com/msbrogli/rpudb',
    install_requires=['pudb'],
)
