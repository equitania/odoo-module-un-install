import setuptools
from odoo_module_un_install.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo-module-un-install-equitania",
    version=__version__,
    author="Equitania Software GmbH",
    author_email="info@equitania.de",
    description="A package to un/install modules in Odoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['odoo_module_un_install'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.8',
    entry_points='''
    [console_scripts]
    odoo-un-install=odoo_module_un_install.odoo_module_un_install:cli
    ''',
    install_requires=[
        'OdooRPC>=0.10.1',
        'click>=8.1.8',
        'PyYaml>=6.0.2',
        'colorama>=0.4.4',
        'tqdm>=4.62.0',
        'keyring>=23.0.0'
    ]
)