FROM ubuntu:16.04

RUN apt-get -y update && apt-get -y install git wget python-dev python3-dev libopenmpi-dev python-pip zlib1g-dev cmake libglib2.0-0 libsm6 libxext6 libfontconfig1 libxrender1
ENV CODE_DIR /root/code
ENV VENV /root/venv

RUN \
    pip install virtualenv && \
    virtualenv $VENV --python=python3 && \
    . $VENV/bin/activate && \
    mkdir $CODE_DIR && \
    cd $CODE_DIR && \
    pip install --upgrade pip && \
    pip install codacy-coverage && \
    pip install scipy && \
    pip install tqdm && \
    pip install joblib && \
    pip install zmq && \
    pip install dill && \
    pip install progressbar2 && \
    pip install mpi4py && \
    pip install cloudpickle && \
    pip install tensorflow==1.5.0 && \
    pip install click && \
    pip install opencv-python && \
    pip install numpy && \
    pip install pandas && \
    pip install pytest==3.5.1 && \
    pip install pytest-cov && \
    pip install matplotlib && \
    pip install seaborn && \
    pip install glob2 && \
    pip install gym[atari,classic_control]>=0.10.9

ENV PATH=$VENV/bin:$PATH

CMD /bin/bash



#
#RUN apt-get -y update && apt-get -y install \
#    git \
#    wget \
#    libopenmpi-dev \
#    zlib1g-dev cmake \
#    libglib2.0-0 \
#    libsm6 \
#    libxext6 \
#    libfontconfig1 \
#    libxrender1\
#    software-properties-common \
#    vim
#
#ENV CODE_DIR /root/code
#ENV VENV /root/venv
#
#
#
## Install python
#RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#    python-numpy \
#    python-dev
#
## Installing python3.6
#RUN \
#    add-apt-repository ppa:jonathonf/python-3.6 && \
#    apt update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#    build-essential \
#    python3.6 \
#    python3.6-dev \
#    python3-pip \
#    python3.6-venv
#
#
#RUN ln -s /usr/bin/python3.6 /usr/local/bin/python3
#
### Installing pip and pip3
##RUN \
##    apt-get remove python-pip python3-pip && \
##    wget https://bootstrap.pypa.io/get-pip.py && \
##    python get-pip.py && \
##    python3 get-pip.py && \
##    rm get-pip.py
#
### Setting up the directories
#RUN mkdir $CODE_DIR
#WORKDIR $CODE_DIR
#RUN git clone https://github.com/pierg/wiseml.git
#RUN git clone https://github.com/pierg/baselines.git
#RUN cd wiseml
#
##RUN \
##    pip install virtualenv && \
##    virtualenv $VENV --python=python3 && \
##    . $VENV/bin/activate
#
#RUN python3 -m pip install pip --upgrade && \
#        python3 -m pip install wheel
#
#RUN \
#    pip3 install --upgrade pip && \
#    pip3 install codacy-coverage && \
#    pip3 install scipy && \
#    pip3 install tqdm && \
#    pip3 install joblib && \
#    pip3 install zmq && \
#    pip3 install dill && \
#    pip3 install progressbar2 && \
#    pip3 install mpi4py && \
#    pip3 install cloudpickle && \
#    pip3 install tensorflow==1.5.0 && \
#    pip3 install click && \
#    pip3 install opencv-python && \
#    pip3 install numpy && \
#    pip3 install pandas && \
#    pip3 install pytest==3.5.1 && \
#    pip3 install pytest-cov && \
#    pip3 install matplotlib && \
#    pip3 install seaborn && \
#    pip3 install glob2 && \
#    pip3 install gym[atari,classic_control]>=0.10.9
#
#RUN \
#    pip3 install PyQt5 && \
#    pip3 install transitions
#
#ENV PATH=$VENV/bin:$PATH
#ENV PYTHONPATH $PYTHONPATH:$CODE_DIR/baselines
#
#ENTRYPOINT ["./entrypoint.sh"]
#CMD [""]
