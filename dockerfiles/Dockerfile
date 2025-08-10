FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_DIR=/opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tcsh \
    python3 \
    python3-pip \
    git \
    curl \
    build-essential \
    gfortran \
    libx11-dev \
    xterm \
    libreadline-dev \
    libncurses-dev \
    wget \
    libglib2.0-0 \
    unzip \
    rsync \
    sudo \
    libxcb1 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxkbcommon-x11-0 \
    libx11-xcb1 \
    libxcb-glx0 \
    libxcb-render-util0 \
    libegl1 \
    libdbus-1-3 \
    mesa-va-drivers \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    mesa-utils \
    libxrender1 \
    libxkbcommon-x11-0 \
    x11-xserver-utils \
    libxcomposite1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libnss3 \
    libasound2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create the 'aips' user
RUN	useradd -md /usr/local/aips -s /bin/bash aips &&\
	echo "aips:aips" | chpasswd &&\
	adduser aips sudo

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p $CONDA_DIR && \
    rm miniconda.sh

# Copy environment and install under 'aips' user
COPY pyside62.yml /tmp/pyside62.yml

USER aips
WORKDIR /home/aips

# Make conda commands available to non-login shell
SHELL ["/bin/bash", "-c"]

RUN conda init bash && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda env create -f /tmp/pyside62.yml && \
    echo "conda activate pyside62" >> ~/.bashrc

ENV PATH=$CONDA_DIR/envs/pyside62/bin:$PATH
ENV CONDA_DEFAULT_ENV=pyside62

# Download and install AIPS
WORKDIR /usr/local/aips
USER aips
ADD	31DEC24 .AIPSRC
RUN wget ftp://ftp.aoc.nrao.edu/pub/software/aips/31DEC24/install.pl && \
    chmod 755 install.pl && \
    ./install.pl -n
    
# Create an AIPS disk
RUN mkdir /usr/local/aips/DISKS &&\
    mkdir /usr/local/aips/DISKS/DISK_1 &&\
    touch /usr/local/aips/DISKS/DISK_1/SPACE &&\
    echo "+  /usr/local/aips/DISKS/DISK_1" >> /usr/local/aips/.dadevs
    
# Add aips shell setup globally
USER root
RUN	printf '\n\
sssin           5000/tcp        SSSIN      # AIPS TV server\n\
ssslock         5002/tcp        SSSLOCK    # AIPS TV Lock\n\
msgserv         5008/tcp        MSGSERV    # AIPS Message Server\n\
tekserv         5009/tcp        TEKSERV    # AIPS TekServer\n\
aipsmt0         5010/tcp        AIPSMT0    # AIPS remote FITS disk access\n\
aipsmt1         5011/tcp        AIPSMT1    # AIPS remote tape 1\n\
aipsmt2         5012/tcp        AIPSMT2    # AIPS remote tape 2\n\
' >> /root/services &&\
	printf '\n# all users should source AIPS\n\
if [ -f /usr/local/aips/LOGIN.SH ]; then\n\
  source /usr/local/aips/LOGIN.SH\n\
fi\n\
' >> /etc/bash.bashrc

# Copy and run VIPCALs
RUN cd /home/aips/ && git clone https://github.com/dalvarezo/VIPCALs.git
RUN chown -R aips:aips /home/aips/VIPCALs
USER aips
WORKDIR /home/aips/VIPCALs
#CMD ["bash"]
CMD ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate pyside62 && source /usr/local/aips/LOGIN.SH && cd /home/aips/VIPCALs/GUI && python3 run_GUI_docker.py"]
#CMD ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate pyside62 && python3 /home/aips/vipcals/GUI/run_GUI.py"]