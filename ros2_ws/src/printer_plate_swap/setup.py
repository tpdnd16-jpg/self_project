from glob import glob

from setuptools import setup

package_name = "printer_plate_swap"

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
    install_requires=["setuptools", "pyyaml"],
    zip_safe=True,
    description="Doosan M0609 3D printer build plate swap",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "swap_node = printer_plate_swap.swap_node:main",
            "print_pose = printer_plate_swap.print_pose:main",
        ],
    },
)
