import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo-module-un-install-equitania",
    version="0.0.2",
    author="Lukas von Ehr - Equitania Software GmbH",
    author_email="l.von.ehr@equitania.de",
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
        'click>=7.1.2',
        'OdooRPC>=0.7.0',
        'PyYaml>=3.12'
    ]
)