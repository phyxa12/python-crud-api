pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        REGISTRY_NAME    = 'python-crud-api'
        CONTAINER_NAME   = 'production-api-container'
        PORT_MAPPING     = '5000:5000'
        VOLUME_NAME      = 'production-api-data'
        DATA_PATH        = '/var/lib/backend_data'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('1. Checkout Code') {
            steps {
                checkout scm
                sh 'echo "Building commit: $(git rev-parse HEAD)"'
            }
        }

        stage('2. Lint Python') {
            steps {
                sh 'python3 -m ruff check app.py test_app.py'
            }
        }

        stage('3. Syntax Check & Unit Test') {
            steps {
                sh 'python3 -m py_compile app.py test_app.py'
                sh 'python3 -m unittest -v test_app.py'
            }
        }

        stage('4. Build Docker Image') {
            steps {
                sh '''
                    set -e
                    GIT_SHORT=$(git rev-parse --short HEAD)
                    echo "Building ${REGISTRY_NAME}:${BUILD_NUMBER} and ${REGISTRY_NAME}:${GIT_SHORT}"
                    docker build -t ${REGISTRY_NAME}:${BUILD_NUMBER} -t ${REGISTRY_NAME}:${GIT_SHORT} .
                    docker tag ${REGISTRY_NAME}:${BUILD_NUMBER} ${REGISTRY_NAME}:latest
                    echo "${GIT_SHORT}" > .image-sha
                '''
            }
        }

        stage('5. Automated Deployment') {
            steps {
                sh '''
                    set -e
                    mkdir -p .deploy
                    PREVIOUS=$(docker inspect --format "{{.Config.Image}}" ${CONTAINER_NAME} 2>/dev/null || true)
                    if [ -n "${PREVIOUS}" ]; then
                        echo "${PREVIOUS}" > .deploy/previous_image.txt
                        echo "Previous image recorded: ${PREVIOUS}"
                    fi
                    docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
                    docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
                    docker volume create ${VOLUME_NAME} >/dev/null
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        -p ${PORT_MAPPING} \
                        -v ${VOLUME_NAME}:${DATA_PATH} \
                        --restart unless-stopped \
                        ${REGISTRY_NAME}:latest
                '''
            }
        }

        stage('6. Health Check') {
            steps {
                sh '''
                    for attempt in $(seq 1 15); do
                        if curl -fsS http://localhost:5000/health; then
                            echo ""
                            echo "Health check passed on attempt ${attempt}"
                            docker logs --tail 20 ${CONTAINER_NAME}
                            exit 0
                        fi
                        echo "Attempt ${attempt}: service not ready yet"
                        sleep 2
                    done
                    echo "Health check failed after 15 attempts"
                    docker ps -a --filter name=${CONTAINER_NAME}
                    docker logs --tail 50 ${CONTAINER_NAME} || true
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully.'
        }
        failure {
            sh 'bash scripts/rollback.sh || true'
            echo 'Pipeline failed. Rollback attempted. Inspect Console Output.'
        }
        always {
            sh 'docker image prune -f --filter "until=168h" >/dev/null 2>&1 || true'
        }
    }
}
