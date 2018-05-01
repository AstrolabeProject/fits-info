FROM ubuntu:16.04
MAINTAINER Tom Hicks

ENV TERM="xterm"

# Install python3 and PIP:
RUN apt-get update && \
    apt-get install -y python3 python3-pip

RUN pip3 install astropy

RUN apt-get remove -y python3-pip && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# mount point for external user data volume
RUN mkdir /data /fits

COPY metadata-keys.txt /fits
COPY fits.py /fits

ENTRYPOINT ["/fits/fits.py"]
CMD ["--help"]
