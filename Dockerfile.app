FROM xshan1/tensorflow:custom

LABEL maintainer="theresa.shan@intel.com"

ARG http_proxy

ARG https_proxy

ENV http_proxy $http_proxy

ENV https_proxy $https_proxy

RUN echo $https_proxy

RUN echo $http_proxy

# Uncomment the two lines below if you wish to use an Ubuntu mirror repository
# that is closer to you (and hence faster). The 'sources.list' file inside the
# 'tools/docker/' folder is set to use one of Ubuntu's official mirror in Taiwan.
# You should update this file based on your own location. For a list of official
# Ubuntu mirror repositories, check out: https://launchpad.net/ubuntu/+archivemirrors
#COPY sources.list /etc/apt
#RUN rm /var/lib/apt/lists/* -vf

RUN apt-get update && apt-get -y install git python-opencv wget protobuf-compiler debconf-utils apt-transport-https python3-pip
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections
RUN apt-get install -y ttf-mscorefonts-installer
RUN fc-cache
RUN pip3 --proxy ${https_proxy} install Flask opencv-python redis==2.10.0 ipython paho-mqtt

RUN mkdir /mobilenet
RUN git config --global http.proxy ${http_proxy}
RUN git config --global https.proxy ${https_proxy}
RUN git clone https://github.com/tensorflow/models.git
RUN wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v1_coco_2017_11_17.tar.gz && \
    tar -xvzf ssd_mobilenet_v1_coco_2017_11_17.tar.gz -C /mobilenet

RUN mkdir /streamapp
RUN cp -R models/research/object_detection /streamapp

# install protoc 3.3
RUN mkdir /protoc_3.3 && cd /protoc_3.3
RUN wget https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip && unzip protoc-3.3.0-linux-x86_64.zip -d /protoc_3.3
RUN cd /streamapp && /protoc_3.3/bin/protoc object_detection/protos/*.proto --python_out=.

WORKDIR /streamapp
RUN sed -i "s#'arial.ttf', 24#'/usr/share/fonts/truetype/msttcorefonts/arial.ttf', 24#g" object_detection/utils/visualization_utils.py
COPY . .

EXPOSE 5000

ENV http_proxy ""
ENV https_proxy ""
