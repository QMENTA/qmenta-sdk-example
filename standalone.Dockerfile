# See https://hub.docker.com/u/qmentasdk/ for more base images

# Install the SDK
FROM ubuntu:18.04

WORKDIR /root

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip wget && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install qmenta-sdk-lib
RUN python3 -m qmenta.sdk.make_entrypoint /root/entrypoint.sh /root/

# Install your software requirements and run other config commands (may take several minutes)
RUN apt-get update -y && \
    apt-get install -y mrtrix libfreetype6-dev libxft-dev wkhtmltopdf xvfb && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install matplotlib numpy pdfkit tornado

# A virtual x framebuffer is required to generate PDF files with pdfkit
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/bin/wkhtmltopdf.sh && \
    chmod a+x /usr/bin/wkhtmltopdf.sh && \
    ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf

# Copy the source files (only this layer will have to be built after the first time)
COPY tool.py report_template.html qmenta_logo.png /root/
