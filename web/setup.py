from distutils.core import setup

from setuptools import find_packages

setup(name='p2k16',
      version='1.0',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      entry_points={
      },
      install_requires=[
          'flask',
          'flask-login',
          'flask-bcrypt',
          'Flask-Bower',
          'Flask-SQLAlchemy',
          'Flask-Testing',
          'flask-mail',
          'typing',
          'psycopg2',
          'sqlalchemy',
          'sqlalchemy-migrate',
          'nose',
          'paho-mqtt',
      ],
      )
