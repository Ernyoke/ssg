from setuptools import setup


def readme():
    with open('README.md') as read_me:
        return read_me.read()


setup(name='ssg',
      version='0.0.1',
      long_description=readme(),
      long_description_content_type='text/markdown',
      classifiers=[],
      url='https://github.com/Ernyoke/ssg',
      author='Ervin Szilagyi',
      auther_email='ervin_szilagyi[at]outlook.com',
      keywords='static site generator',
      license='MIT',
      packages=['ssg'],
      install_requires=['markdown', 'beautifulsoup4'],
      include_pacage_data=True,
      zip_safe=False)
