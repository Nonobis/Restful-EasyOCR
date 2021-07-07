FROM pytorch/pytorch

# if you forked EasyOCR, you can pass in your own GitHub username to use your fork
# i.e. gh_username=myname
ARG gh_username=Nonobis
ARG service_home="/home/EasyOCR"

ENV SERVER_PORT 8200
ENV SERVER_HOST 0.0.0.0

# https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(Native-GPU-Support)
ENV USE_GPU true
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Configure apt and install packages
RUN apt-get update -y && \
    apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-dev \
    git \
    # cleanup
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/li


# Clone EasyOCR repo
RUN mkdir "$service_home" \
    && git clone "https://github.com/$gh_username/EasyOCR.git" "$service_home" \
    && cd "$service_home" \
    && git remote add upstream "https://github.com/$gh_username/EasyOCR.git" \
    && git pull upstream master

# Build
RUN cd "$service_home"

# install requirements for easyOCR inside a virtual env
RUN  pip install -r requirements.txt
    
# Build EasyOCR
RUN  python setup.py build_ext --inplace -j 4 \
    && python -m pip install -e .

# Upload Data Folder
RUN mkdir "$service_home/data" 

ADD ./recognition.py /home/ubuntu/
WORKDIR /home/ubuntu/

# Install flask for API
RUN pip install Flask

EXPOSE 2000
RUN alias python=python3
ENTRYPOINT ["python"]
CMD ["/home/ubuntu/recognition.py"]
