~~For Documentation manual please visit [this page](https://softwaredevelopmentvimmo.readthedocs.io/en/latest/)~~ (STILL IN DEVELOPMENT)

# SoftwareDevelopmentVIMMO

# VIMMO

A Flask-based API application for panel data analysis.

## Installation

### Prerequisites

- Conda (Miniconda or Anaconda)
- Git.
### For Docker
- Docker Desktop

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/VIMMO.git
cd SoftwareDevelopmentVIMMO/
```

2. Create and activate the conda environment:
```bash
# Create the conda environment from environment.yaml
conda env create -f environment.yaml

# Activate the environment
conda activate VIMMO
```

3. Install the package using pyproject.toml:
The package installation will automatically handle all dependencies listed in `pyproject.toml`.
```bash
# Install in development mode
pip install -e .
```

## Usage

After installation, you can run the API server:
```bash
# Using the console script
vimmo

```
OR


## Build using Docker
```bash
# to run docker make sure you are in route directory of the project
cd <your_file_path>/SoftwareDevelopmentVIMMO


# make sure your docker daemon is running by starting the docker desktop
# Note: requires docker desktop to use the docker compose command

# # to build the image and to run the container 
docker compose up --build

# to run it in the background use
docker compose up -d --build

#to exit and remove
docker stop my_vimmo_app
docker rm my_vimmo_app
```

The API will be available at:
- Main API: http://127.0.0.1:5001/
- Swagger UI Documentation: http://127.0.0.1:5001/

# For endpoint information please refer to User guide in docs/vimmo.pdf


## Testing

Make sure you are in root directory (<you_file_path>/SoftwareDevelopmentVIMMO/) :
Testing requires an instance of the application to be running depending on the test type you will be running as it checks for various live responses
Please run the App in a seperate terminal or have an instance of Docker running in the background in port 5001
```bash
pytest #Tests everything requires (vimmo api to run in the background/new terminal)

# for extra debugging purposes use 
pytest -s # this prints out some of the info we recieve and should only be used for debugging purposes e.g, change in panelapp or variant validator.

# To test just integration
pytest -m integration

# To test just unittest modules
 pytest -m "not integration" #Note: this does not require an instance of the app to run as it mocks responses with dummy data

```


## Change Logging Levels
To change the logging levels, need to modify the source code before building the application
in the folder vimmo/logger/logging_config.py
```bash
# Set file loggin on line 17 to required options [DEBUG, INFO, WARNING, ERROR, CRITICAL]
logger.setLevel(logging.DEBUG) # making the default logger at DEBUG level to log all messages


#Set console log level on line 29 to required options [DEBUG, INFO, WARNING, ERROR, CRITICAL]
console_handler.setLevel(logging.CRITICAL) # Logs INFO level and  above to the console
```


## Schedule Database Updates

To set up a scheduled cron job on your system to update the 
panel database, run the following command:

```bash
# this will prompt you for input...
dbscheduler
```

### Choose a Schedule

When prompted, type a number and press **Enter** to select the desired schedule:

1. **Every minute**  
2. **Every day at midnight**  
3. **Every week at midnight (Sunday)**  
4. **Every month at midnight (1st)**  
5. **Remove schedule**  

**Enter your choice (1-5):**

### Managing Scheduled Updates

Entering **5** in the dbscheduler will remove the scheduled update. Alternatively, you can use the following commands:

```bash
# To list cron jobs
crontab -l

# To edit the crontab (e.g. to further customise schedule)
crontab -e

# To remove all cron jobs
crontab -r
````




## Version Update for developer purposes
Use after git commit -m "message"
```bash
# Patch version (0.1.0 → 0.1.1) 
bumpversion patch

# Minor version (0.1.0 → 0.2.0):
bumpversion minor

# Major version (0.1.0 → 1.0.0):
bumpversion major
```




### Building the Package for Production ( purpose but not being used for easy code changes)

If you want to build the distribution files:
```bash
# This will create both wheel and source distribution
python -m build
```

This will create:
- A wheel file (*.whl) in the `dist/` directory
- A source distribution (*.tar.gz) in the `dist/` directory

Install using:
```bash
# This will create both wheel and source distribution
pip install dist/*.whl
```



