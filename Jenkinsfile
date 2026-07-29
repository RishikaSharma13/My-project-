pipeline {
    agent any

    parameters {

        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'prod'],
            description: 'Select deployment environment'
        )

        booleanParam(
            name: 'FAIL_ON_VULNERABILITIES',
            defaultValue: false,
            description: 'Fail pipeline if CRITICAL vulnerabilities are found'
        )
    }

    environment {
        IMAGE_NAME = "image-to-sketch"
        AWS_REGION = "ap-south-1"
        ECR_REPO = "150619449649.dkr.ecr.ap-south-1.amazonaws.com/image-to-sketch"

        SCANNER_HOME = tool 'SonarScanner'

        TRIVY_TEMPLATE = "trivy/html.tpl"

        BUILD_IMAGE_TAG = "build-${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/RishikaSharma13/My-project-.git'
            }
        }

        stage('Pipeline Configuration') {
            steps {
                script {

                    echo "=================================="
                    echo "Pipeline Configuration"
                    echo "Environment              : ${params.ENVIRONMENT}"
                    echo "Fail On Vulnerabilities  : ${params.FAIL_ON_VULNERABILITIES}"
                    echo "Build Tag                : ${BUILD_IMAGE_TAG}"
                    echo "=================================="

                }
            }
        }

        stage('Set Environment Variables') {
            steps {
                script {

                    env.DEPLOY_PATH = "/opt/image-to-sketch"

                    if (params.ENVIRONMENT == 'dev') {

                        env.LATEST_TAG = "latest-dev"
                        env.COMPOSE_FILE = "docker-compose.dev.yml"
                        env.APP_PORT = "4001"

                    } else {

                        env.LATEST_TAG = "latest-prod"
                        env.COMPOSE_FILE = "docker-compose.prod.yml"
                        env.APP_PORT = "4000"

                    }

                    echo "=================================="
                    echo "Environment Variables"
                    echo "BUILD TAG     : ${BUILD_IMAGE_TAG}"
                    echo "LATEST TAG    : ${LATEST_TAG}"
                    echo "DEPLOY_PATH   : ${DEPLOY_PATH}"
                    echo "COMPOSE_FILE  : ${COMPOSE_FILE}"
                    echo "APP_PORT      : ${APP_PORT}"
                    echo "=================================="
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                    $SCANNER_HOME/bin/sonar-scanner
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                echo "Building Docker Image..."

                docker build -t $IMAGE_NAME:$BUILD_IMAGE_TAG .

                echo "Creating latest tag..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $IMAGE_NAME:$LATEST_TAG

                docker images | grep $IMAGE_NAME
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                mkdir -p reports

                echo "========================================="
                echo "Running Trivy Security Scan..."
                echo "========================================="

                trivy image \
                  --severity HIGH,CRITICAL \
                  --format table \
                  --output reports/trivy-report.txt \
                  $IMAGE_NAME:$BUILD_IMAGE_TAG

                trivy image \
                  --severity HIGH,CRITICAL \
                  --format template \
                  --template "@${TRIVY_TEMPLATE}" \
                  --output reports/trivy-report.html \
                  $IMAGE_NAME:$BUILD_IMAGE_TAG

                echo ""
                echo "========== Trivy Scan Summary =========="

                cat reports/trivy-report.txt

                echo "========================================"
                '''
            }
        }

        stage('Security Policy Check') {
            steps {
                script {

                    if (params.FAIL_ON_VULNERABILITIES) {

                        echo "Security policy enabled."

                        sh '''
                        trivy image \
                          --severity CRITICAL \
                          --exit-code 1 \
                          $IMAGE_NAME:$BUILD_IMAGE_TAG
                        '''

                    } else {

                        echo "Security policy disabled."
                    }

                }
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                sh '''
                aws ecr get-login-password --region $AWS_REGION | \
                docker login \
                --username AWS \
                --password-stdin 150619449649.dkr.ecr.ap-south-1.amazonaws.com
                '''
            }
        }

        stage('Push Image to Amazon ECR') {
            steps {
                sh '''
                echo "Pushing immutable image..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $ECR_REPO:$BUILD_IMAGE_TAG

                docker push \
                    $ECR_REPO:$BUILD_IMAGE_TAG

                echo "Updating latest environment tag..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $ECR_REPO:$LATEST_TAG

                docker push \
                    $ECR_REPO:$LATEST_TAG

                echo "Images pushed successfully."
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                cd $DEPLOY_PATH

                docker compose -f $COMPOSE_FILE pull

                docker compose -f $COMPOSE_FILE down

                docker compose -f $COMPOSE_FILE up -d --remove-orphans

                docker image prune -f
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh """
                sleep 10

                curl -f http://localhost:${APP_PORT}/health
                """
            }
        }
    }

    post {

        always {
            archiveArtifacts artifacts: 'reports/*', fingerprint: true
        }

        success {
            echo "Pipeline completed successfully!"
        }

        failure {
            echo "Pipeline failed!"
        }
    }
}