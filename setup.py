from distutils.core import setup

setup(
    name='advanced_config_manager',
    version='0.9a1',
    packages=['AdvConfigMgr', 'AdvConfigMgr.docs', 'AdvConfigMgr.tests', 'AdvConfigMgr.utils'],
    url='http://advanced-config-manager.rtfd.org/',
    license='GNU GPL v2',
    author='Dan Strohl',
    author_email='dan@wjcg.net',
    description='Advanced Configuration Manager',
    classifiers=['Development Status :: 2 - Pre-Alpha', 'Environment :: Plugins', 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)', 'Natural Language :: English',
                 'Operating System :: OS Independent','Programming Language :: Python',
                 'Topic :: Software Development :: Libraries :: Python Modules', 'Topic :: Utilities'],
    keywords='configuration INI database migration config setup plugin tool cli startup',


)
