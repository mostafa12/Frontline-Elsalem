from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in frontline_elsalem/__init__.py
from frontline_elsalem import __version__ as version

setup(
	name="frontline_elsalem",
	version=version,
	description="New Custom App by Frontline",
	author="Al-Salem Holding",
	author_email="erp@alsalemholding.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
