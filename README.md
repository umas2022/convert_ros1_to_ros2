# ROS1 to ROS2 Package Converter

This script converts a ROS1 robot description package to a ROS2 package format based on the structure of the `leader_3215_description` packages.

## Features

The converter handles the following transformations:

1. **Directory Structure**:
   - Creates proper ROS2 package structure
   - Converts mesh directory structure (separate collision and visual meshes)
   - Copies configuration and texture directories

2. **URDF to XACRO**:
   - Converts URDF files to XACRO format
   - Updates mesh paths to separate collision and visual references

3. **Package Management**:
   - Converts `package.xml` from ROS1 format (format="2") to ROS2 format (format="3")
   - Updates dependencies for ROS2 compatibility
   - Changes build type to `ament_python`

4. **Python Setup**:
   - Creates `setup.py` for ROS2 Python packages
   - Creates `setup.cfg` with proper installation paths
   - Creates resource directory with marker file

5. **Launch Files**:
   - Creates ROS2 Python launch files
   - Configures robot_state_publisher, joint_state_publisher_gui, and RVIZ nodes

6. **Visualization**:
   - Creates default RVIZ configuration file

## Usage

Run the conversion script:

```bash
python convert_ros1_to_ros2.py
```

The script will convert the ROS1 package located at `ros1/leader_3215_description` to a ROS2 package at `ros2_converted/leader_3215_description`.

## Customization

To convert different packages, modify the paths in the `if __name__ == '__main__':` section of the script:

```python
# Define paths
ros1_package_path = 'path/to/your/ros1/package'
ros2_package_path = 'path/to/your/output/ros2/package'
```

## Package Structure

### Input ROS1 Package Structure:
```
leader_3215_description/
├── config/
├── launch/
│   ├── display.launch
│   └── gazebo.launch
├── meshes/
│   ├── base_link.STL
│   ├── link1.STL
│   └── ...
├── urdf/
│   └── leader_3215_description.urdf
├── CMakeLists.txt
└── package.xml
```

### Output ROS2 Package Structure:
```
leader_3215_description/
├── config/
├── launch/
│   └── launch.py
├── meshes/
│   ├── collision/
│   │   ├── base_link.STL
│   │   ├── link1.STL
│   │   └── ...
│   └── visual/
│       ├── base_link.STL
│       ├── link1.STL
│       └── ...
├── resource/
│   └── leader_3215_description
├── rviz/
│   └── default.rviz
├── urdf/
│   └── leader_3215_description.xacro
├── package.xml
├── setup.cfg
└── setup.py
```

## Requirements

- Python 3.x
- ROS2 (for using the converted package)

## Building the Converted Package

After conversion, build the ROS2 package:

```bash
cd ros2_converted/leader_3215_description
colcon build
```

## Running the Converted Package

Source the workspace and run the launch file:

```bash
source install/setup.bash
ros2 launch leader_3215_description launch.py
```