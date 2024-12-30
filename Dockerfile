FROM python:3.13

ENV PATH="/root/miniconda3/bin:${PATH}"

# Update the package list and install required packages
RUN apt-get update && apt-get -y upgrade && apt-get install -y sqlite3 cron git wget

# Download and install Miniconda
RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ]; then \
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"; \
    elif [ "$arch" = "aarch64" ]; then \
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"; \
    else \
    echo "Unsupported architecture: $arch"; \
    exit 1; \
    fi && \
    wget $MINICONDA_URL -O miniconda.sh && \
    bash miniconda.sh -b -p /root/miniconda3 && \
    rm -f miniconda.sh

# Clone the repository
RUN git clone --branch docker-test --single-branch https://github.com/Itebbs22/SoftwareDevelopmentVIMMO /app

WORKDIR /app

# Create the Conda environment
RUN conda init bash && \
    bash -c "source /root/.bashrc && conda env create -f environment.yaml"

# Activate the Conda environment in all shells
RUN echo "source /root/miniconda3/etc/profile.d/conda.sh && conda activate VIMMO" >> ~/.bashrc

# Ensure the default shell uses Conda
SHELL ["bash", "-l", "-c"]

# Upgrade pip
RUN pip install --upgrade pip

RUN pip install -e .

RUN cron

# Optional: Default command to run the container
CMD tail -f /dev/null
