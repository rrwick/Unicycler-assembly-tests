#!/usr/bin/env python3
"""
Run 'python3 setup.py install' to install Unicycler assembly tests.
"""

# Make sure this is being run with Python 3.4 or later.
import sys
if sys.version_info.major != 3 or sys.version_info.minor < 4:
    sys.exit('Error: you must execute setup.py using Python 3.4 or later')

import os
import shutil
import importlib.util

# Install setuptools if not already present.
if not importlib.util.find_spec("setuptools"):
    import ez_setup
    ez_setup.use_setuptools()

from setuptools import setup
from setuptools.command.install import install

# Make sure we're running from the setup.py directory.
script_dir = os.path.dirname(os.path.realpath(__file__))
if script_dir != os.getcwd():
    os.chdir(script_dir)

with open('README.md', 'rb') as readme:
    LONG_DESCRIPTION = readme.read().decode()


class UnicyclerAssemblyTestsInstall(install):
    """
    The install process copies the C++ shared library to the install location.
    """
    user_options = install.user_options + [
        ('makeargs=', None, 'Arguments to be given to make')
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.makeargs = None

    if __name__ == '__main__':
        def run(self):
            install.run(self)
            shutil.copyfile('model_qc_clr', os.path.join(self.install_lib,
                                                         'unicycler_assembly_tests',
                                                         'model_qc_clr'))


setup(name='unicycler_assembly_tests',
      description='Unicycler assembly tests',
      long_description=LONG_DESCRIPTION,
      url='http://github.com/rrwick/unicycler_assembly_tests',
      author='Ryan Wick',
      author_email='rrwick@gmail.com',
      license='GPL',
      packages=['unicycler_assembly_tests'],
      entry_points={"console_scripts": ['assembler_comparison = '
                                        'unicycler_assembly_tests.assembler_comparison:main',
                                        'generate_illumina_reads = '
                                        'unicycler_assembly_tests.generate_illumina_reads:main',
                                        'generate_long_reads = '
                                        'unicycler_assembly_tests.generate_long_reads:main']},
      zip_safe=False,
      cmdclass={'install': UnicyclerAssemblyTestsInstall}
      )
