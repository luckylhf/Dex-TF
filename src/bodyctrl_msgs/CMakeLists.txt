cmake_minimum_required(VERSION 3.8)
project(bodyctrl_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
#
# 本包是纯 rosidl 接口包（只有 msg/ srv/，无任何 C++ 源码），因此只需要：
#   ament_cmake                 —— 构建工具
#   rosidl_default_generators   —— 接口代码生成
#   std_msgs / geometry_msgs / builtin_interfaces
#                               —— 接口定义中【实际用到】的类型
#
# 以下 find_package 曾存在但均未被使用，已移除（避免干净环境下 rosdep
# 装不齐导致 CMake 配置失败，并缩短构建时间）：
#   rclcpp / rclcpp_components  —— 无 C++ 节点、无组件注册
#   sensor_msgs                 —— 42 个 .msg / 22 个 .srv 均未引用其类型
#   yaml-cpp                    —— 无 C++ 代码使用；且其 rosdep 键为
#                                  yaml_cpp_vendor（会从源码编译，开销大）
find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)


# generate msgs and srvs
file(GLOB MSG_SOURCES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "${CMAKE_CURRENT_SOURCE_DIR}/msg/*.msg")
file(GLOB SRV_SOURCES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "${CMAKE_CURRENT_SOURCE_DIR}/srv/*.srv")
rosidl_generate_interfaces(${PROJECT_NAME}
  ${MSG_SOURCES}
  ${SRV_SOURCES}
  # Add packages that above messages depend on, in this case geometry_msgs for Sphere.msg
  DEPENDENCIES std_msgs geometry_msgs builtin_interfaces
)
ament_export_dependencies(rosidl_default_runtime)
# 说明: 此处原有一个 rosidl_get_typesupport_target() 调用，用于把本包的
# C++ typesupport 目标导出给同包内的 C++ 节点链接。本包无 C++ 源码，
# 该变量从未被使用，已移除；下游包如需链接本包类型，可自行调用：
#   rosidl_get_typesupport_target(target ${PROJECT_NAME} rosidl_typesupport_cpp)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
