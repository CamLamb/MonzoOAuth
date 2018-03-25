from setuptools import setup

setup(
    name='MonzoOAuth',
    version='0.2.0',
    description='An OAuth2 Monzo Client',
    url='https://github.com/jafacakes2011/MonzoOAuth',
    author='Cameron',
    author_email='',
    license='MIT',
    packages=['MonzoOAuth'],
    install_requires=[
      'oauth2client',
    ],
    zip_safe=False
)