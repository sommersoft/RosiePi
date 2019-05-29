from setuptools import setup, find_packages
setup(
    name="rosiepi",
    version="0.1",
    # metadata to display on PyPI
    author="Michael Schroeder",
    author_email="sommersoft@gmail.com",
    description="CircuitPython Firmware Test Framework",
    license="MIT",
    keywords="circuitpython, rosiepi, rosie",
    url="https://github.com/sommersoft/RosiePi",   # project home page, if any
    project_urls={
        "Issues": "https://github.com/sommersoft/RosiePi/issues",
        #"Documentation": "https://docs.example.com/HelloWorld/",
        "Source Code": "https://github.com/sommersoft/RosiePi",
    },

    # could also include long_description, download_url, classifiers, etc.

    #scripts=['rosie_scripts/test_control_unit.py'],

    #install_requires=[],

    packages=["rosiepi"],

    #package_dir={"":"rosiepi"},
    package_data={
        "": ["rosie_scripts/bash_scripts/*.sh",
             "board_data/test_files/*/*.py",
             "board_data/firmware/*.uf2",
             "board_test_configs/*.json"]
    },

    entry_points={
        "console_scripts": [
            "rosiepi = rosiepi.rosie_scripts.test_manager:start_test"
        ]
    }
)
