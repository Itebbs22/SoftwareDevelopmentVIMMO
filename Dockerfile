# Use Miniconda as the base image
FROM continuumio/miniconda3

# Set the working directory to /app
WORKDIR /app

# Copy environment file
COPY environment.yaml /app/environment.yaml

# Create Conda environment with the correct name
RUN conda env create -f /app/environment.yaml && conda clean -afy

# Activate Conda environment and set PATH
SHELL ["/bin/bash", "-c"]
RUN echo "conda activate VIMMO" >> ~/.bashrc
ENV PATH /opt/conda/envs/VIMMO/bin:$PATH

# Copy application files
COPY . /app

# Install test dependencies
RUN /bin/bash -c "source ~/.bashrc && conda activate VIMMO && pip install -e .[test]"

# Expose port 5000 to the outside world
EXPOSE 5000

# Run the application (main.py) when the container starts
CMD ["/bin/bash", "-c", "source ~/.bashrc && conda activate VIMMO && vimmo"]
