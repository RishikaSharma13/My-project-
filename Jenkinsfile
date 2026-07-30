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

        DEPLOY_PATH = "/opt/image-to-sketch"
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

                echo "Creating latest-dev tag..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $IMAGE_NAME:latest-dev

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

                echo "Updating latest-dev tag..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $ECR_REPO:latest-dev

                docker push \
                    $ECR_REPO:latest-dev

                echo "Images pushed successfully."
                '''
            }
        }

        stage('Deploy Dev') {
            steps {
                sh '''
                echo "Deploying to Development..."

                cd $DEPLOY_PATH

                docker compose -f docker-compose.dev.yml pull

                docker compose -f docker-compose.dev.yml down

                docker compose -f docker-compose.dev.yml up -d --remove-orphans
                '''
            }
        }

        stage('Health Check - Dev') {
            steps {
                sh '''
                echo "Checking Development Health..."

                sleep 10

                curl -f http://localhost:4001/health
                '''
            }
        }

        stage('Deploy Prod') {
            steps {
                sh '''
                echo "Deploying to Production..."

                cd $DEPLOY_PATH

                docker compose -f docker-compose.prod.yml pull

                docker compose -f docker-compose.prod.yml down

                docker compose -f docker-compose.prod.yml up -d --remove-orphans

                docker image prune -f
                '''
            }
        }

        stage('Health Check - Prod') {
            steps {
                sh '''
                echo "Checking Production Health..."

                sleep 10

                curl -f http://localhost:4000/health
                '''
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