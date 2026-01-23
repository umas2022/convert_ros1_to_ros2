import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/mnt/c/Users/umas_local/Documents/user/ws_local/ws_code/self/convert_ros1_to_ros2/example/bp001/ros2/install/bp001_description'
