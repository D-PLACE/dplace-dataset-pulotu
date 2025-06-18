from setuptools import setup, find_packages


setup(
    name='cldfbench_pulotu',
    py_modules=['cldfbench_pulotu'],
    packages=find_packages(where='.'),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'pulotu=cldfbench_pulotu:Dataset',
        ],
        'cldfbench.commands': [
            'pulotu=pulotu_commands',
        ],
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
