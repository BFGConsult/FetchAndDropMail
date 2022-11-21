from setuptools import setup

setup(name='FetchAndDropMail',
      version='0.1',
      description='Fetch mail from an email account and drop it somewhere',
      url='https://github.com/BFGConsult/FetchAndDropMail',
      author='BFG',
      author_email='bfg@bfgconsult.no',
      license='GPL-3.0',
      py_modules=['FetchAndDropMail'],
      install_requires=[
          'pyyaml',
      ],
      zip_safe=False)
