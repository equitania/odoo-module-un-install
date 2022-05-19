import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo-module-un-install-equitania",
    version="0.0.3",
    author="Equitania Software GmbH",
    author_email="info@equitania.de",
    description="A package to un/install modules in Odoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['odoo_module_un_install'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points='''
    [console_scripts]
    odoo-un-install=odoo_module_un_install.odoo_module_un_install:start_odoo_module_un_install
    ''',
    install_requires=[
        'OdooRPC>=0.8.0',
        'click>=8.1.3',
        'PyYaml>=6.0'
    ]
)