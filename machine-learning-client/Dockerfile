# base this image on a Debian release with Python installed
FROM python:3.9-bullseye 

# update the package manager
RUN apt-get update

# install the OpenCV cv2 dependencies missing from the Docker image
RUN apt-get install -y ffmpeg libsm6 libxext6  -y

# install the ALSA sound drivers missing from the Docker image
# RUN apt-get install -y alsa-base alsa-utils
RUN apt-get install -y alsa-utils

# install the Python dependencies
RUN pip install --upgrade pip
RUN pip install pipenv

# create a directory for the app
RUN mkdir /app

# make the app directory the current working directory within the image
WORKDIR /app

# create a non-root user to use when running the container
# our use of `&&` helps with caching
RUN useradd -m -r beetroot && chown beetroot /app

# switch to our non-root user
USER beetroot

# copy the Pipfiles and install the dependencies... doing this fist may save build time via caching
COPY Pipfile* .

# install the app dependencies
RUN pipenv install

# copy all the files from the current directory to the app directory
COPY . .

# when a container is instantiated, run the target script
CMD ["pipenv", "run", "python", "find_camera_devices.py"]
