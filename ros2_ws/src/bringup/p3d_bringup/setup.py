from glob import glob

from setuptools import setup

package_name = "p3d_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    description="전체 시스템 launch 와 설정",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
        ],
    },
)
