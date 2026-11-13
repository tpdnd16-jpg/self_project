from glob import glob

from setuptools import setup

package_name = "p3d_task_manager"

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
    description="제어 모듈: 공정 상태 머신 (출력 완료 → 플레이트 교체 → 다음 출력)",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "task_manager_node = p3d_task_manager.task_manager_node:main",
        ],
    },
)
