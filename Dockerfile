# Define global args
ARG FUNCTION_DIR="/home/app/"
ARG VERSION="3.8"

# Use a smaller base image
FROM python:${VERSION}-slim AS base

# Upgrade pip
RUN pip install --upgrade pip

# Create the /home/app directory
RUN mkdir -p /home/app

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Install Lambda Runtime Interface Client for Python
RUN pip install awslambdaric

# Install dependencies
RUN pip install torch==1.9.0+cpu torchvision==0.10.0+cpu facenet_pytorch -f https://download.pytorch.org/whl/torch_stable.html

# Copy function code
COPY entry.sh /
COPY requirements.txt handler.py ${FUNCTION_DIR}/

RUN pip install -r requirements.txt

# Install AWS Lambda Runtime Interface Emulator
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
RUN chmod 755 /usr/bin/aws-lambda-rie

# Set permissions
RUN chmod 777 /entry.sh && \
    chmod -R 777 /home/app

# Set the CMD to your handler
ENTRYPOINT [ "/entry.sh" ]
CMD [ "handler.handler" ]