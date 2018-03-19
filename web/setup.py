from distutils.core import setup

from setuptools import find_packages

setup(name='p2k16',
      version='1.0',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      entry_points={
      },
      install_requires=[
          'emails',
          'flask',
          'flask-bcrypt',
          'flask-bower',
          'flask-env',
          'flask_inputs>=0.2.0',
          'flask-login',
          'flask-sqlalchemy',
          'flask-testing',
          'gunicorn',
          'jsonschema',
          'ldif3',
          'nose',
          'paho-mqtt',
          'psycopg2-binary',
          'sqlalchemy',
          'sqlalchemy-continuum',
          'stripe',
          'typing',
      ],
      dependency_links=[
          'git+https://github.com/nathancahill/flask-inputs.git@9d7d329#egg=Flask_Inputs-9d7d329',
      ])
