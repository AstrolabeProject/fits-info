FROM ubuntu:16.04
MAINTAINER Tom Hicks

ENV TERM="xterm"

# Install python3
RUN apt-get update && \
    apt-get install -y python3 python3-pip

RUN pip3 install astropy

RUN apt-get remove -y python3-pip && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# these are really for the singularity container for the UofA HPC:
RUN mkdir /xdisk
RUN mkdir /extra
RUN mkdir /rsgrps

# ENV PYTHONPATH=".:/usr/local/lib/python3"

COPY fits.py /
COPY metadata-keys.txt /

ENTRYPOINT ["/fits.py"]
