void setBuildStatus(String message, String state) {
  step([
      $class: "GitHubCommitStatusSetter",
      reposSource: [$class: "ManuallyEnteredRepositorySource", url: "https://github.com/Mani-varma1/SoftwareDevelopmentVIMMO"],
      contextSource: [$class: "ManuallyEnteredCommitContextSource", context: "ci/jenkins/build-status"],
      errorHandlers: [[$class: "ChangingBuildStatusErrorHandler", result: "UNSTABLE"]],
      statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}

pipeline {
    agent {
        docker {
            image 'continuumio/miniconda3:latest'
            args '-u root -v /var/run/docker.sock:/var/run/docker.sock --network host'
        }
    }

    environment {
        CONDA_ENV_NAME = 'VIMMO'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Docker') {
            steps {
                sh '''
                    # Add Docker's official GPG key
                    apt-get update
                    apt-get install -y ca-certificates curl gnupg
                    install -m 0755 -d /etc/apt/keyrings
                    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                    chmod a+r /etc/apt/keyrings/docker.gpg

                    # Add Docker repository
                    echo \
                      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
                      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
                      tee /etc/apt/sources.list.d/docker.list > /dev/null

                    # Install Docker and Docker Compose
                    apt-get update
                    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                '''
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''#!/bin/bash
                    # Initialize conda for shell interaction
                    conda init bash
                    source ~/.bashrc
                    
                    # Create and activate environment
                    conda env create -f environment.yaml
                    
                    # Activate environment with full path to avoid conda init issues
                    source $(conda info --base)/etc/profile.d/conda.sh
                    conda activate ${CONDA_ENV_NAME}
                    
                    # Install package
                    pip install -e .[test]
                '''
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh '''#!/bin/bash
                    source $(conda info --base)/etc/profile.d/conda.sh
                    conda activate ${CONDA_ENV_NAME}
                    pytest -m "not integration"
                '''
            }
        }

        stage('Test Docker Image and Run Integration Tests') {
            steps {
                sh '''#!/bin/bash
                    source $(conda info --base)/etc/profile.d/conda.sh
                    conda activate ${CONDA_ENV_NAME}
                    
                    # Create a custom network for the tests
                    docker network create vimmo_test_network || true
                    
                    # Start the application with specific network settings
                    docker compose up -d --build
                    
                    echo "Waiting for services to be ready..."
                    
                    # More robust wait for the service
                    attempt_counter=0
                    max_attempts=30
                    
                    until curl -s http://localhost:5000/health > /dev/null || [ $attempt_counter -eq $max_attempts ]; do
                        printf '.'
                        attempt_counter=$(($attempt_counter+1))
                        sleep 2
                    done
                    
                    if [ $attempt_counter -eq $max_attempts ]; then
                        echo "Failed to connect to the API after 60 seconds"
                        docker compose logs
                        exit 1
                    fi
                    
                    echo "Service is up, running tests..."
                    pytest -m "integration"
                '''
            }
        }
    }

    post {
        success {
            setBuildStatus("Build succeeded", "SUCCESS");
        }
        failure {
            setBuildStatus("Build failed", "FAILURE");
        }
        always {
            sh '''#!/bin/bash
                # Use docker compose v2 command syntax
                docker compose down --volumes --remove-orphans
                docker network rm vimmo_test_network || true
                
                # Cleanup Conda environment
                source $(conda info --base)/etc/profile.d/conda.sh
                conda deactivate
                conda env remove -n ${CONDA_ENV_NAME} -y || true
            '''
        }
    }
}