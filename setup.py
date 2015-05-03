import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    name='advanced_config_manager',
    version='1.0',
    packages=['AdvConfigMgr', 'AdvConfigMgr.docs', 'AdvConfigMgr.tests', 'AdvConfigMgr.utils'],
    url='http://advanced-config-manager.rtfd.org/',
    license='GNU GPL v2',
    author='Dan Strohl',
    author_email='dan@wjcg.net',
    description='Advanced Configuration Manager',
    long_description=README,
    install_requires=['pathutils', 'python_log_indenter', ],
    classifiers=['Development Status :: 2 - Pre-Alpha', 'Environment :: Plugins', 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)', 'Natural Language :: English',
                 'Operating System :: OS Independent', 'Programming Language :: Python',
                 'Topic :: Software Development :: Libraries :: Python Modules', 'Topic :: Utilities',
                 'Framework :: Django'],
    keywords='configuration INI database migration config setup plugin tool cli startup'
)
