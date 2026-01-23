#!/usr/bin/env python3

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

def convert_ros1_to_ros2(ros1_package_path, ros2_package_path):
    """
    Convert a ROS1 package to a ROS2 package based on the structure of leader_3215_description.
    
    Args:
        ros1_package_path (str): Path to the ROS1 package
        ros2_package_path (str): Path where the ROS2 package should be created
    """
    print(f"Converting ROS1 package at {ros1_package_path} to ROS2 package at {ros2_package_path}")
    
    # Create the ROS2 package directory structure
    Path(ros2_package_path).mkdir(parents=True, exist_ok=True)
    
    # Copy config directory if it exists
    ros1_config_path = os.path.join(ros1_package_path, 'config')
    ros2_config_path = os.path.join(ros2_package_path, 'config')
    if os.path.exists(ros1_config_path):
        print("Copying config directory")
        shutil.copytree(ros1_config_path, ros2_config_path, dirs_exist_ok=True)
    
    # Copy textures directory if it exists
    ros1_textures_path = os.path.join(ros1_package_path, 'textures')
    ros2_textures_path = os.path.join(ros2_package_path, 'textures')
    if os.path.exists(ros1_textures_path):
        print("Copying textures directory")
        shutil.copytree(ros1_textures_path, ros2_textures_path, dirs_exist_ok=True)
    
    # Handle meshes directory - ROS2 uses separate collision and visual subdirectories
    ros1_meshes_path = os.path.join(ros1_package_path, 'meshes')
    if os.path.exists(ros1_meshes_path):
        print("Converting meshes directory structure")
        ros2_meshes_path = os.path.join(ros2_package_path, 'meshes')
        collision_path = os.path.join(ros2_meshes_path, 'collision')
        visual_path = os.path.join(ros2_meshes_path, 'visual')
        Path(collision_path).mkdir(parents=True, exist_ok=True)
        Path(visual_path).mkdir(parents=True, exist_ok=True)
        
        # Copy all mesh files to both collision and visual directories
        for mesh_file in os.listdir(ros1_meshes_path):
            if mesh_file.endswith('.STL'):
                src_mesh = os.path.join(ros1_meshes_path, mesh_file)
                shutil.copy2(src_mesh, os.path.join(collision_path, mesh_file))
                shutil.copy2(src_mesh, os.path.join(visual_path, mesh_file))
    
    # Convert URDF to XACRO
    convert_urdf_to_xacro(ros1_package_path, ros2_package_path)
    
    # Create or convert package.xml
    convert_package_xml(ros1_package_path, ros2_package_path)
    
    # Create setup.py for ROS2
    create_setup_py(ros1_package_path, ros2_package_path)
    
    # Create setup.cfg
    create_setup_cfg(ros2_package_path)
    
    # Create RVIZ directory and configuration
    create_rviz_config(ros2_package_path)
    
    # Convert launch files
    convert_launch_files(ros1_package_path, ros2_package_path)
    
    # Create resource directory
    create_resource_directory(ros2_package_path)
    
    print("Conversion completed successfully!")

def convert_urdf_to_xacro(ros1_package_path, ros2_package_path):
    """Convert URDF file to XACRO format with separate collision and visual meshes."""
    ros1_urdf_path = os.path.join(ros1_package_path, 'urdf')
    ros2_urdf_path = os.path.join(ros2_package_path, 'urdf')
    Path(ros2_urdf_path).mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(ros1_urdf_path):
        print("No URDF directory found in ROS1 package")
        return
    
    # Get package name from package.xml
    package_name = os.path.basename(ros2_package_path)
    package_xml_path = os.path.join(ros2_package_path, 'package.xml')
    
    if os.path.exists(package_xml_path):
        try:
            tree = ET.parse(package_xml_path)
            root = tree.getroot()
            name_element = root.find('name')
            if name_element is not None and name_element.text:
                package_name = name_element.text
        except:
            pass  # Use directory name if parsing fails
    
    for urdf_file in os.listdir(ros1_urdf_path):
        if urdf_file.endswith('.urdf'):
            print(f"Converting URDF file: {urdf_file}")
            src_urdf = os.path.join(ros1_urdf_path, urdf_file)
            # Change extension from .urdf to .xacro
            xacro_filename = urdf_file.replace('.urdf', '.xacro')
            dst_xacro = os.path.join(ros2_urdf_path, xacro_filename)
            
            # Read the URDF file
            with open(src_urdf, 'r') as f:
                urdf_content = f.read()
            
            # Create the base package path to replace
            original_package_path = ''
            # Extract package name from original URDF content
            import re
            package_matches = re.findall(r'package://([^/]+)/', urdf_content)
            if package_matches:
                original_package_path = package_matches[0]
            else:
                # If no package name found, try to infer from directory
                original_package_path = os.path.basename(ros1_package_path)
            
            # First, replace all mesh paths with visual paths
            xacro_content = urdf_content.replace(
                f'package://{original_package_path}/meshes/',
                f'package://{package_name}/meshes/visual/'
            )
            
            # Now, replace visual paths with collision paths in collision blocks
            # This requires proper XML-aware processing to avoid changing visual paths outside collision blocks
            lines = xacro_content.split('\n')
            new_lines = []
            in_collision_block = False
            
            for line in lines:
                modified_line = line
                if '<collision>' in line and '</collision>' not in line:
                    # Start of collision block
                    in_collision_block = True
                    new_lines.append(modified_line)
                elif '</collision>' in line:
                    # End of collision block
                    in_collision_block = False
                    new_lines.append(modified_line)
                elif '<collision' in line and '>' in line and not in_collision_block:
                    # Self-closing collision tag
                    new_lines.append(modified_line)
                elif in_collision_block and 'filename="package://' in line:
                    # Inside collision block, replace visual path with collision path
                    modified_line = line.replace(
                        f'package://{package_name}/meshes/visual/',
                        f'package://{package_name}/meshes/collision/'
                    )
                    new_lines.append(modified_line)
                else:
                    # Outside collision block, keep as is
                    new_lines.append(modified_line)
            
            xacro_content = '\n'.join(new_lines)
            
            # Write the XACRO file
            with open(dst_xacro, 'w') as f:
                f.write(xacro_content)

def convert_package_xml(ros1_package_path, ros2_package_path):
    """Convert ROS1 package.xml to ROS2 format."""
    ros1_pkg_xml = os.path.join(ros1_package_path, 'package.xml')
    ros2_pkg_xml = os.path.join(ros2_package_path, 'package.xml')
    
    if not os.path.exists(ros1_pkg_xml):
        print("No package.xml found in ROS1 package, creating default ROS2 package.xml")
        create_default_package_xml(ros2_package_path)
        return
    
    print("Converting package.xml from ROS1 to ROS2 format")
    
    # Parse the ROS1 package.xml
    tree = ET.parse(ros1_pkg_xml)
    root = tree.getroot()
    
    # Update package format
    root.set('format', '3')
    
    # Add XML model header
    # Note: ElementTree doesn't preserve processing instructions, so we'll add them when writing
    
    # Update buildtool_depend from catkin to ament_cmake
    for buildtool in root.findall('buildtool_depend'):
        if buildtool.text == 'catkin':
            buildtool.text = 'ament_cmake'
    
    # Update dependencies for ROS2
    # Remove roslaunch dependency
    for depend in root.findall('depend'):
        if depend.text == 'roslaunch':
            root.remove(depend)
    
    # Update gazebo dependency
    for depend in root.findall('depend'):
        if depend.text == 'gazebo':
            depend.text = 'gazebo_ros'
    
    # Update rviz dependency to rviz2
    for depend in root.findall('depend'):
        if depend.text == 'rviz':
            depend.text = 'rviz2'
    
    # Add build_depend and exec_depend for launch_ros
    build_depend = ET.SubElement(root, 'build_depend')
    build_depend.text = 'launch_ros'
    
    exec_depend = ET.SubElement(root, 'exec_depend')
    exec_depend.text = 'launch_ros'
    
    # Update build_type in export section
    export = root.find('export')
    if export is None:
        export = ET.SubElement(root, 'export')
    
    build_type = export.find('build_type')
    if build_type is None:
        build_type = ET.SubElement(export, 'build_type')
    build_type.text = 'ament_python'
    
    # Write the updated package.xml with proper XML declaration and model header
    with open(ros2_pkg_xml, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>\n')
        f.write(ET.tostring(root, encoding='unicode'))

def create_default_package_xml(ros2_package_path):
    """Create a default ROS2 package.xml file."""
    # Get package name from directory name
    package_name = os.path.basename(ros2_package_path)
    
    package_xml_content = f'''<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>{package_name}</name>
  <version>0.1.0</version>
  <description>{package_name}</description>
  <maintainer email="{package_name}@umas.com">{package_name}</maintainer>
  <license>none</license>

  <depend>urdf</depend>
  <build_depend>launch_ros</build_depend>
  <exec_depend>launch_ros</exec_depend>
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>joint_state_publisher_gui</exec_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
'''
    
    ros2_pkg_xml = os.path.join(ros2_package_path, 'package.xml')
    with open(ros2_pkg_xml, 'w') as f:
        f.write(package_xml_content)

def create_setup_py(ros1_package_path, ros2_package_path):
    """Create setup.py for ROS2 package."""
    print("Creating setup.py for ROS2 package")
    
    # Get package name from directory name or package.xml
    package_name = os.path.basename(ros2_package_path)
    package_xml_path = os.path.join(ros2_package_path, 'package.xml')
    
    if os.path.exists(package_xml_path):
        try:
            tree = ET.parse(package_xml_path)
            root = tree.getroot()
            name_element = root.find('name')
            if name_element is not None and name_element.text:
                package_name = name_element.text
        except:
            pass  # Use directory name if parsing fails
    
    setup_py_content = f'''from setuptools import setup
from glob import glob

package_name = '{package_name}'

setup(
    name=package_name,
    version='0.0.0',
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, glob('launch/*.py')),
        ('share/' + package_name+'/urdf/', glob('urdf/*')),
        ('share/' + package_name+'/rviz/', glob('rviz/*')),
        ('share/' + package_name+'/meshes/collision/', glob('meshes/collision/*')),
        ('share/' + package_name+'/meshes/visual/', glob('meshes/visual/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros-industrial',
    maintainer_email='TODO:',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={{
        'console_scripts': [
        ],
    }},
)
'''
    
    setup_py_path = os.path.join(ros2_package_path, 'setup.py')
    with open(setup_py_path, 'w') as f:
        f.write(setup_py_content)
    
    # Create resource directory and empty resource file
    resource_dir = os.path.join(ros2_package_path, 'resource')
    Path(resource_dir).mkdir(parents=True, exist_ok=True)
    resource_file = os.path.join(resource_dir, package_name)
    with open(resource_file, 'w') as f:
        pass  # Create empty file

def create_setup_cfg(ros2_package_path):
    """Create setup.cfg for ROS2 package."""
    print("Creating setup.cfg")
    
    # Get package name from directory name initially
    package_name = os.path.basename(ros2_package_path)
    
    # Check if package.xml exists and get the actual package name from it
    package_xml_path = os.path.join(ros2_package_path, 'package.xml')
    
    if os.path.exists(package_xml_path):
        try:
            tree = ET.parse(package_xml_path)
            root = tree.getroot()
            name_element = root.find('name')
            if name_element is not None and name_element.text:
                package_name = name_element.text
        except:
            pass  # Use directory name if parsing fails
    
    setup_cfg_content = f'''[develop]
script_dir=$base/lib/{package_name}
[install]
install_scripts=$base/lib/{package_name}
'''
    
    setup_cfg_path = os.path.join(ros2_package_path, 'setup.cfg')
    with open(setup_cfg_path, 'w') as f:
        f.write(setup_cfg_content)

def create_rviz_config(ros2_package_path):
    """Create a basic RVIZ configuration file."""
    print("Creating RVIZ configuration")
    rviz_dir = os.path.join(ros2_package_path, 'rviz')
    Path(rviz_dir).mkdir(parents=True, exist_ok=True)
    
    rviz_config_content = '''Panels:
  - Class: rviz_common/Displays
    Help Height: 78
    Name: Displays
    Property Tree Widget:
      Expanded:
        - /Global Options1
        - /Status1
      Splitter Ratio: 0.5
    Tree Height: 549
  - Class: rviz_common/Selection
    Name: Selection
  - Class: rviz_common/Tool Properties
    Expanded:
      - /2D Goal Pose1
      - /Publish Point1
    Name: Tool Properties
    Splitter Ratio: 0.5886790156364441
Visualization Manager:
  Class: ""
  Displays:
    - Alpha: 0.5
      Cell Size: 1
      Class: rviz_default_plugins/Grid
      Color: 160; 160; 164
      Enabled: true
      Name: Grid
    - Alpha: 1
      Class: rviz_default_plugins/RobotModel
      Collision Enabled: false
      Description Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /robot_description
      Enabled: true
      Name: RobotModel
      Visual Enabled: true
  Enabled: true
  Global Options:
    Background Color: 48; 48; 48
    Fixed Frame: base_link
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz_default_plugins/Interact
      Hide Inactive Objects: true
    - Class: rviz_default_plugins/MoveCamera
    - Class: rviz_default_plugins/Select
    - Class: rviz_default_plugins/FocusCamera
    - Class: rviz_default_plugins/Measure
      Line color: 128; 128; 0
    - Class: rviz_default_plugins/SetInitialPose
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /initialpose
    - Class: rviz_default_plugins/SetGoal
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /goal_pose
    - Class: rviz_default_plugins/PublishPoint
      Single click: true
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /clicked_point
  Transformation:
    Current:
      Class: rviz_default_plugins/TF
  Value: true
  Views:
    Current:
      Class: rviz_default_plugins/Orbit
      Distance: 1.5
      Enable Stereo Rendering:
        Stereo Eye Separation: 0.05999999865889549
        Stereo Focal Distance: 1
        Swap Stereo Eyes: false
        Value: false
      Focal Point:
        X: 0
        Y: 0
        Z: 0
      Focal Shape Fixed Size: true
      Focal Shape Size: 0.05000000074505806
      Invert Z Axis: false
      Name: Current View
      Near Clip Distance: 0.009999999776482582
      Pitch: 0.37039801478385925
      Target Frame: <Fixed Frame>
      Value: Orbit (rviz)
      Yaw: 1.8362867832183838
    Saved: ~
Window Geometry:
  Displays:
    collapsed: false
  Height: 846
  Hide Left Dock: false
  Hide Right Dock: false
  QMainWindow State: 000000ff00000000fd000000040000000000000156000002b0fc0200000008fb0000001200530065006c0065006300740069006f006e00000001e10000009b0000005c00fffffffb0000001e0054006f006f006c002000500072006f007000650072007400690065007302000001ed000001df00000185000000a3fb000000120056006900650077007300200054006f006f02000001df000002110000018500000122fb000000200054006f006f006c002000500072006f0070006500720074006900650073003203000002880000011d000002210000017afb000000100044006900730070006c006100790073010000003d000002b0000000c900fffffffb0000002000730065006c0065006300740069006f006e00200062007500660066006500720200000138000000aa0000023a00000294fb00000014005700690064006500530074006500720065006f02000000e6000000d2000003ee0000030bfb0000000c004b0069006e0065006300740200000186000001060000030c00000261000000010000010f000002b0fc0200000003fb0000001e0054006f006f006c002000500072006f00700065007200740069006500730100000041000000780000000000000000fb0000000a00560069006500770073010000003d000002b0000000a400fffffffb0000001200530065006c0065006300740069006f006e010000025a000000b200000000000000000000000200000490000000a9fc0100000001fb0000000a00560069006500770073030000004e00000080000002e10000019700000003000004420000003efc0100000002fb0000000800540069006d00650100000000000004420000000000000000fb0000000800540069006d006501000000000000045000000000000000000000023f000002b000000004000000040000000800000008fc0000000100000002000000010000000a0054006f006f006c00730100000000ffffffff0000000000000000
'''

    rviz_config_file = os.path.join(rviz_dir, 'default.rviz')
    with open(rviz_config_file, 'w') as f:
        f.write(rviz_config_content)

def create_resource_directory(ros2_package_path):
    """Create the resource directory with the marker file."""
    print("Creating resource directory")
    resource_dir = os.path.join(ros2_package_path, 'resource')
    Path(resource_dir).mkdir(parents=True, exist_ok=True)
    
    # Get package name
    package_name = os.path.basename(ros2_package_path)
    package_xml_path = os.path.join(ros2_package_path, 'package.xml')
    
    if os.path.exists(package_xml_path):
        try:
            tree = ET.parse(package_xml_path)
            root = tree.getroot()
            name_element = root.find('name')
            if name_element is not None and name_element.text:
                package_name = name_element.text
        except:
            pass  # Use directory name if parsing fails
    
    # Create empty resource file
    resource_file = os.path.join(resource_dir, package_name)
    with open(resource_file, 'w') as f:
        pass  # Create empty file

def convert_launch_files(ros1_package_path, ros2_package_path):
    """Convert ROS1 launch files to ROS2 launch files."""
    ros1_launch_path = os.path.join(ros1_package_path, 'launch')
    ros2_launch_path = os.path.join(ros2_package_path, 'launch')
    
    if not os.path.exists(ros1_launch_path):
        print("No launch directory found in ROS1 package")
        return
    
    print("Converting launch files to ROS2 format")
    Path(ros2_launch_path).mkdir(parents=True, exist_ok=True)
    
    # Create a single ROS2 launch.py file instead of converting each .launch file
    ros2_launch_file = os.path.join(ros2_launch_path, 'launch.py')
    
    # Get package name from package.xml
    package_name = os.path.basename(ros2_package_path)
    package_xml_path = os.path.join(ros2_package_path, 'package.xml')
    
    if os.path.exists(package_xml_path):
        try:
            tree = ET.parse(package_xml_path)
            root = tree.getroot()
            name_element = root.find('name')
            if name_element is not None and name_element.text:
                package_name = name_element.text
        except:
            pass  # Use directory name if parsing fails
    
    create_ros2_launch_file(ros2_launch_file, package_name=package_name)

def create_ros2_launch_file(ros2_launch_file, package_name=None):
    """Create a ROS2 launch.py file based on the template."""
    # Get package name from the launch file path if not provided
    if package_name is None:
        package_dir_name = os.path.dirname(os.path.dirname(ros2_launch_file))  # Get parent of launch dir
        package_name = os.path.basename(package_dir_name)
    
    template_launch_content = f'''import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command


def generate_launch_description():
    # Get the launch directory
    package_dir = get_package_share_directory('{package_name}')

    # Launch configuration variables specific to simulation
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_joint_state_pub = LaunchConfiguration('use_joint_state_pub')
    use_rviz = LaunchConfiguration('use_rviz')
    urdf_file = LaunchConfiguration('urdf_file')
    xacro_args = LaunchConfiguration('xacro_args')

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        'rviz_config_file',
        default_value=os.path.join(package_dir, 'rviz', 'default.rviz'),
        description='Full path to the RVIZ config file to use')
    declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
        'use_robot_state_pub',
        default_value='True',
        description='Whether to start the robot state publisher')
    declare_use_joint_state_pub_cmd = DeclareLaunchArgument(
        'use_joint_state_pub',
        default_value='True',
        description='Whether to start the joint state publisher')
    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='Whether to start RVIZ')

    declare_urdf_cmd = DeclareLaunchArgument(
        'urdf_file',
        default_value=os.path.join(package_dir, 'urdf', '{package_name}.xacro'),
        description='Name of the used URDF file')

    declare_xacro_cmd = DeclareLaunchArgument(
        'xacro_args',
        default_value="",
        description='Arguments for xacro')

    robot_description = ParameterValue(Command(['xacro ',
                                                xacro_args,
                                                " ",
                                                urdf_file]),  # you can add your xacro arguments here
                                       value_type=str)

    start_robot_state_publisher_cmd = Node(
        condition=IfCondition(use_robot_state_pub),
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        # parameters=[{{'use_sim_time': use_sim_time}}],
        parameters=[{{
            'robot_description': robot_description}}])

    start_joint_state_publisher_cmd = Node(
        condition=IfCondition(use_joint_state_pub),
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen')

    rviz_cmd = Node(
        condition=IfCondition(use_rviz),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen')

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_rviz_config_file_cmd)
    ld.add_action(declare_urdf_cmd)
    ld.add_action(declare_xacro_cmd)
    ld.add_action(declare_use_robot_state_pub_cmd)
    ld.add_action(declare_use_joint_state_pub_cmd)
    ld.add_action(declare_use_rviz_cmd)

    # Add any conditioned actions
    ld.add_action(start_joint_state_publisher_cmd)
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(rviz_cmd)

    return ld
'''
    
    with open(ros2_launch_file, 'w') as f:
        f.write(template_launch_content)

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert a ROS1 package to ROS2 format')
    parser.add_argument('--ros1-path', type=str, default='example/bp001/ros1/bp001_description')
    parser.add_argument('--ros2-path', type=str, default='example/bp001/ros2/bp001_description')
    
    args = parser.parse_args()
    
    # Perform the conversion
    convert_ros1_to_ros2(args.ros1_path, args.ros2_path)
    
    print(f"\nROS1 to ROS2 conversion complete!")
    print(f"Converted package is located at: {args.ros2_path}")
