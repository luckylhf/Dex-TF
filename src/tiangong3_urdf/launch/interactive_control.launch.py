import launch
from launch.substitutions import (
    Command,
    LaunchConfiguration,
    PathJoinSubstitution,
    FindExecutable,
)
import launch_ros
import os
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = launch_ros.substitutions.FindPackageShare(
        package="tiangong3_urdf"
    ).find("tiangong3_urdf")

    default_model_path = os.path.join(pkg_share, "urdf", "tiangong3.urdf.xacro")
    default_rviz_config_path = os.path.join(pkg_share, "config", "interactive.rviz")

    args = []
    args.append(
        launch.actions.DeclareLaunchArgument(
            name="model",
            default_value=default_model_path,
            description="Absolute path to Tiangong Dex URDF file",
        )
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            LaunchConfiguration("model"),
        ]
    )
    robot_description_param = {
        "robot_description": launch_ros.parameter_descriptions.ParameterValue(
            robot_description_content, value_type=str
        )
    }

    robot_state_publisher_node = launch_ros.actions.Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[robot_description_param],
    )

    real_status_bridge_node = launch_ros.actions.Node(
        package="tiangong3_urdf",
        executable="joint_state_publisher.py",
        name="real_status_bridge",
        output="screen",
    )

    interactive_gui_node = launch_ros.actions.Node(
        package="tiangong3_urdf",
        executable="interactive_gui.py",
        name="interactive_gui",
        output="screen",
    )

    rviz_node = launch_ros.actions.Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", default_rviz_config_path],
    )

    nodes = [
        robot_state_publisher_node,
        real_status_bridge_node,
        interactive_gui_node,
        rviz_node,
    ]

    return launch.LaunchDescription(args + nodes)
