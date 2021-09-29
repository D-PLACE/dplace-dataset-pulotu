from setuptools import setup


setup(
    name='cldfbench_pulotu',
    py_modules=['cldfbench_pulotu'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'pulotu=cldfbench_pulotu:Dataset',
        ]
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
