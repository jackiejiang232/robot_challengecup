# Robot Test Client

这个目录是文旅机器人比赛环境的最小移动测试 client。

## 结论

`docker pull crpi-1pzq998p9m7w0auy.cn-hangzhou.personal.cr.aliyuncs.com/challengecup/material_sorting:latest`
会把官方镜像下载到本机 Docker 的镜像库里。它不是普通文件夹，不会自动出现在当前目录；只有 `docker run` 启动容器后，镜像里的 `/workspace/supermarket_sorting_task` 才会作为容器文件系统出现。

你自己的算法推荐以 ROS2 client 的形式运行，和官方 server 使用相同的：

- `--network host`
- `ROS_DOMAIN_ID=99`
- `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`

server 负责仿真、机器人模型、场景、传感器、裁判；client 通过 ROS2 topic 订阅传感器/指令并发布控制指令。

## 启动固定场景 server

先允许 Docker 访问图形窗口并创建缓存卷：

```bash
xhost +local:docker
docker volume create material_sorting_cache
```

如果当前用户没有 Docker 权限，把下面命令前面的 `docker` 改成 `sudo docker`。

```bash
docker run --rm -it \
  --gpus all \
  --network host \
  --ipc host \
  --name material_sorting_server \
  -e DISPLAY=${DISPLAY} \
  -e ROS_DOMAIN_ID=99 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  -e MUJOCO_GL=glfw \
  -e MATERIAL_ENABLE_RENDER=1 \
  -e MATERIAL_USE_GS=1 \
  -e MATERIAL_RANDOMIZE=0 \
  -e MATERIAL_ENABLE_SCORE=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v material_sorting_cache:/opt/torch_ext \
  crpi-1pzq998p9m7w0auy.cn-hangzhou.personal.cr.aliyuncs.com/challengecup/material_sorting:latest \
  python3 examples/material_sorting/material_sorting_server.py
```

## 运行移动测试

另开一个终端运行：

```bash
docker run --rm -it \
  --network host \
  --ipc host \
  -e ROS_DOMAIN_ID=99 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  -v /home/jiangzhenmin/Desktop/挑战杯/robot_test_client:/client:ro \
  crpi-1pzq998p9m7w0auy.cn-hangzhou.personal.cr.aliyuncs.com/challengecup/material_sorting:latest \
  python3 /client/move_test.py
```

脚本会向 `/cmd_vel` 发布：

- `linear.x=0.15`，前进 2 秒
- 停车
- `angular.z=0.45`，原地转 2 秒
- 停车

可以改参数，例如只轻微前进：

```bash
docker run --rm -it \
  --network host \
  --ipc host \
  -e ROS_DOMAIN_ID=99 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  -v /home/jiangzhenmin/Desktop/挑战杯/robot_test_client:/client:ro \
  crpi-1pzq998p9m7w0auy.cn-hangzhou.personal.cr.aliyuncs.com/challengecup/material_sorting:latest \
  python3 /client/move_test.py --linear 0.08 --forward-sec 1.0 --turn-sec 0.0
```

## 后续算法怎么写

典型 client 循环是：

1. 订阅 `/material/instruction`，读取 JSON 指令。
2. 订阅 `/head_camera/color/image_raw`、深度图、相机内参，或者直接启动官方 baseline 感知节点并订阅 `/material/detections`。
3. 订阅 `/slamware_ros_sdk_server_node/odom` 和 `/joint_states` 获取机器人状态。
4. 发布 `/cmd_vel` 控制底盘。
5. 发布 `/spine_forward_position_controller/commands`、`/head_forward_position_controller/commands`、左右臂 controller topics 控制升降、头和双臂。
6. 订阅 `/referee/gameinfo`、`/referee/score` 调试任务进度。
