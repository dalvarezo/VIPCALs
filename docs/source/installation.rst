How to install
==============

The pipeline is available in two forms:

- As a **pip-installable Python package**, which requires a working AIPS installation.
- As a **Docker container**, which simplifies the setup

The Docker container is easy to use, but building and running it requires `sudo` privileges. A **Singularity image** is currently being worked on, which will allow the pipeline to run on servers without `sudo` access.

----

Requirements
------------

Before installing, make sure you have the following software available:

Manual installation:
~~~~~~~~~~~~~~~~~~~~

- AIPS 31DEC24 or newer
- Conda

Docker installation:
~~~~~~~~~~~~~~~~~~~~

- Docker
- XQuartz (only in MacOS)
- sudo privileges

----

Installation
------------

Getting the pipeline up and running is simple. Below we describe the recommended steps for the different installations.

Manual Installation
~~~~~~~~~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/dalvarezo/VIPCALs.git

2. Create the conda environment:

   .. code-block:: bash

      cd VIPCALs
      conda env create -f vipcalsenv.yml

3. Activate the conda environment and install with:

   .. code-block:: bash

      conda activate vipcalsenv
      pip install .

You can now launch VIPCALs with:

.. code-block:: bash

   vipcals

.. note::
   The conda environment was called ``pyside62`` in versions up to 0.3.7 and is now called ``vipcalsenv``. If you are upgrading from an older version, create the new environment as in step 2 and install VIPCALs again inside it. The old environment can then be removed with ``conda env remove -n pyside62``.

AIPS has to be available in the shell where VIPCALs runs. If your AIPS installation is not set up automatically when you open a terminal, run its login script first, for example:

.. code-block:: bash

   source /path/to/AIPS/LOGIN.SH

To update an existing installation, pull the latest changes and install again with ``pip install .`` inside the activated environment.

Docker Installation
~~~~~~~~~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/dalvarezo/VIPCALs.git

2. Build the Docker container:

   .. code-block:: bash

      sudo docker build -t vipcals ./VIPCALs/dockerfiles/

3. Run it (Linux):

   .. code-block:: bash

      sudo docker run -it --rm --net=host \
        -e DISPLAY=$DISPLAY \
        -e QT_X11_NO_MITSHM=1 \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v /your_directory/:/home/vipcals vipcals

   or (MacOS)
   
   .. code-block:: bash

      xhost +127.0.0.1
      docker run -it \
        -e DISPLAY=host.docker.internal:0 \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v /your_directory/:/home/vipcals vipcals

   where `/your_directory/` has to be replaced with the local directory where you wish to work. This directory should contain your data and any subfolders you want the pipeline to access.

   In MacOS, make sure that both DockerDesktop and XQuartz are running, and that XQuartz → Preferences → Security → "Allow connections from network clients" is checked on.
