"""ros2 launch printer_plate_swap plate_swap.launch.py dry_run:=true"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    default_cfg = os.path.join(
        get_package_share_directory("printer_plate_swap"), "config", "plate_swap.yaml"
    )
    return LaunchDescription([
        DeclareLaunchArgument("config_file", default_value=default_cfg),
        DeclareLaunchArgument("dry_run", default_value="false"),
        DeclareLaunchArgument("run_on_start", default_value="false"),
        Node(
            package="printer_plate_swap",
            executable="swap_node",
            output="screen",
            emulate_tty=True,
            parameters=[{
                "config_file": LaunchConfiguration("config_file"),
                "dry_run": ParameterValue(LaunchConfiguration("dry_run"), value_type=bool),
                "run_on_start": ParameterValue(LaunchConfiguration("run_on_start"), value_type=bool),
            }],
        ),
    ])
