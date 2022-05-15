from setuptools import setup


def readme():
    with open('README.md') as read_me:
        return read_me.read()


setup(name='ssg',
      version='0.0.4',
      long_description=readme(),
      long_description_content_type='text/markdown',
      classifiers=[],
      url='https://github.com/Ernyoke/ssg',
      author='Ervin Szilagyi',
      author_email='ervin_szilagyi[at]outlook.com',
      keywords='static site generator',
      license='MIT',
      packages=['ssg'],
      install_requires=['markdown', 'beautifulsoup4', 'python-slugify'],
      include_pacage_data=True,
      entry_points={
            'console_scripts': ['ssg=ssg.command_line:main'],
      },
      zip_safe=False)
