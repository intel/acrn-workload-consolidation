# Workload Consolidation - Industrial Edge to Cloud Demo
This repo hosts demo code designed to showcase the workload consolidation feature of [Project ACRN](https://projectacrn.org/) on edge devices.

## Demo Video
[![Workload-Consolidation-Demo-Video](https://img.youtube.com/vi/Z0HUBUHzBbk/0.jpg)](https://youtu.be/Z0HUBUHzBbk)

## Getting ready on Edge and Cloud
The demo has been containerized as two deployments for edge and cloud respectively. Before the deployment, here are some prerequisites.  
1. Clone this repository locally: `git clone https://gitlab.devtools.intel.com/ssp-demos/ACRN/industrial-edge-demo.git`
2. Make sure [Docker](https://www.docker.com/) is running: `sudo systemctl start docker`. If you have not installed Docker yet, please refer to the [installation guide](https://docs.docker.com/install/linux/docker-ce/ubuntu/) to set up docker
3. Follow these on-line instructions: [Docker Compose installation](https://docs.docker.com/compose/install/) and have docker-compose installed
4. Put yourself in the cloned folder: `cd industrial-edge-demo`

## Set up services on edge
There are four services running on the edge device: stream-web, stream-buffer, redis and mosquitto. Here are the steps to start the deployment:
1. Setup proxy in `docker-compose.yml` file if you are building in Intel network and build service images:
```
sudo docker-compose -f docker-compose.yml build
```
Alternatively, the images could be pulled by Dockerhub:
```
sudo docker pull xshan1/industrial-edge-demo_stream-buffer:latest
sudo docker pull xshan1/industrial-edge-demo_stream-web:latest
sudo docker tag xshan1/industrial-edge-demo_stream-buffer:latest industrial-edge-demo_stream-buffer:latest
sudo docker tag xshan1/industrial-edge-demo_stream-web:latest industrial-edge-demo_stream-web:latest
```
2. Set-up the IP camera following the online [User Guides](http://www.sv3c.com/Instruction-and-Software-For-H-264-POE-and-Wired-IP-Camera-L-series-.html)
3. Configure the IP camera video url by setting `CAMERA_SRC=http://ip_cam_hostname:port/xxx` in `docker-compose.yml`
   If you are using a usb web camera, set `CAMERA_SRC=<device id>` and uncomment the lines below.
```
  #devices:
     #- "/dev/video0:/dev/video0"
```
Update the device id by your actual device id. eg. set `CAMERA_SRC=1` and `devices: - "/dev/video1:/dev/video1"`

4. Start the services and all the services are running in the background. 
```
sudo /usr/local/bin/docker-compose up -d 
```
Check the logs:
```
sudo /usr/local/bin/docker-compose logs 
```
Check container status:
```
sudo /usr/local/bin/docker-compose ps -a 
```
5. Tear down the services
```
sudo /usr/local/bin/docker-compose down 
```


## Set up services on the Cloud:
There are seven services running on the Cloud: mongo, redis, mongosetup, mongo-express, rest-api, video-compressor, dashboard. Here are the steps to start the deployment:
1. Setup proxy in `docker-compose-cloud.yml` file if you are building in Intel network and build service images:
```
cd industrial-edge-demo
sudo docker-compose -f docker-compose-cloud.yml build
```
Or the images could be pulled from Dockerhub:
```
sudo docker pull xshan1/industrial-edge-demo_dashboard:latest
sudo docker pull xshan1/industrial-edge-demo_rest-api:latest
sudo docker pull xshan1/industrial-edge-demo_mongosetup:latest
sudo docker pull xshan1/industrial-edge-demo_video-compressor:latest
sudo docker tag xshan1/industrial-edge-demo_dashboard:latest industrial-edge-demo_dashboard:latest
sudo docker tag xshan1/industrial-edge-demo_rest-api:latest industrial-edge-demo_rest-api:latest
sudo docker tag xshan1/industrial-edge-demo_mongosetup:latest industrial-edge-demo_mongosetup:latest
sudo docker tag xshan1/industrial-edge-demo_video-compressor:latest industrial-edge-demo_video-compressor:latest
```
2. Create two directories on the host for mongodb and video files respectively:
```
sudo mkdir -p /data
sudo mkdir -p /video
```
3. Configure `MOSQUITTO_HOST` and `REDIS_HOST` for the video-compressor service:
```
video-compressor:
    ...
    command: ["/usr/bin/python3", "-u", "video_compressor.py"]
    environment:
      - "REDIS_HOST=<ip addr of edge device>"
      - "MOSQUITTO_HOST=<ip addr of edge device>"
      - "REST_API=rest-api"
```
4. Configure `REST_API`, `WS_SERVER`, `TIMEZONE`, `GEO_LAT` and `GEO_LON` for dashboard; Open file `vue-table/src/config.js` and update content as below:
```
export const CONFIG = Object.freeze({
    REST_API: "http://<ip addr of cloud device>:3000",
    WS_SERVER: "ws://<ip addr of edge device>:9001"
    TIMEZONE: "Asia/Shanghai",
    GEO_LAT: 47.413220,
    GEO_LON: -1.219482,
});

```
Replace both `<ip addr of cloud device>` and `<ip addr of edge device>` with the actual Cloud and Edge device IP addresses (respectively). Update the timezone and geo-location accordingly as well. If you are uncertain about your timezone name, you may refer to this [list](https://github.com/moment/moment-timezone/blob/develop/data/packed/latest.json).

5. Start all the services in the background
```
sudo docker-compose -f docker-compose-cloud.yml up -d
```
6. Browse the dashboard: `http://<cloud-host-ip>:8080`


## Set up cyclic test agent on ACRN service OS
The agent watches the real-time changes on the cyclic test log file and sends the accumulated result to the Cloud by mosquitto service. 
1. Checkout the repo on the SOS
```
git clone https://gitlab.devtools.intel.com/ssp-demos/ACRN/industrial-edge-demo.git
cd industrial-edge-demo
```
2. Make sure that `Python >= 3.5` has been installed as well as the python dependencies
```
pip3 install pyinotify paho-mqtt
```
3. Start the agent
```
./cyclic_test_agent.py <path/to/zephyr.log> -s <ip addr mqtt_host> -p <ip addr mqtt_port> -d
```
You may check `cyclic_test_agent.py -h` for help in details.  
```
