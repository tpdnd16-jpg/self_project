cmake_minimum_required(VERSION 3.8)
project(p3d_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RobotState.msg"
  "msg/PrinterStatus.msg"
  "msg/TaskStatus.msg"
  "srv/MoveToPose.srv"
  "srv/GripperCommand.srv"
  "srv/PrinterCommand.srv"
  "action/SwapPlate.action"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
