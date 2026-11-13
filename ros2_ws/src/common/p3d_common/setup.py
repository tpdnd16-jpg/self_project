from glob import glob

from setuptools import setup

package_name = "p3d_common"

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
    description="공통 모듈: 토픽/서비스 이름, 좌표 유틸, 설정 로더",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
        ],
    },
)
