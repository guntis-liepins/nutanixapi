from setuptools import setup,find_packages

classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3',
          ]

setup(name='nutanixapi',
      version='0.1',
      description='Simplified Nutanix API library',
      lond_description="Simplified Nutanix API library",
      author='Guntis Liepins',
      author_email='turbiina@gmail.com',
      url='n/a',
      license='MIT',
      classifiers=classifiers,
      keywords='',
      packages=find_packages(),
      install_requires=['urllib3','requests','jinja2','pathlib','sphinx','humanfriendly']
     )
