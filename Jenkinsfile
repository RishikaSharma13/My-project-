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
                    echo "=================================="

                }
            }
        }

        stage('Set Environment Variables') {
            steps {
                script {

                    env.DEPLOY_PATH = "/opt/image-to-sketch"

                    if (params.ENVIRONMENT == 'dev') {

                        env.IMAGE_TAG = "dev"
                        env.COMPOSE_FILE = "docker-compose.dev.yml"
                        env.APP_PORT = "4001"

                    } else {

                        env.IMAGE_TAG = "prod"
                        env.COMPOSE_FILE = "docker-compose.prod.yml"
                        env.APP_PORT = "4000"

                    }

                    echo "=================================="
                    echo "Environment Variables"
                    echo "IMAGE_TAG    : ${env.IMAGE_TAG}"
                    echo "DEPLOY_PATH  : ${env.DEPLOY_PATH}"
                    echo "COMPOSE_FILE : ${env.COMPOSE_FILE}"
                    echo "APP_PORT     : ${env.APP_PORT}"
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
                docker build -t $IMAGE_NAME:$IMAGE_TAG .
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
                  $IMAGE_NAME:$IMAGE_TAG

                trivy image \
                  --severity HIGH,CRITICAL \
                  --format template \
                  --template "@${TRIVY_TEMPLATE}" \
                  --output reports/trivy-report.html \
                  $IMAGE_NAME:$IMAGE_TAG

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
                        echo "Pipeline will fail if CRITICAL vulnerabilities are found."

                        sh '''
                        trivy image \
                          --severity CRITICAL \
                          --exit-code 1 \
                          $IMAGE_NAME:$IMAGE_TAG
                        '''

                    } else {

                        echo "Security policy disabled."
                        echo "Pipeline will continue even if vulnerabilities exist."

                    }
                }
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                sh '''
                aws ecr get-login-password --region $AWS_REGION | \
                docker login --username AWS --password-stdin 150619449649.dkr.ecr.ap-south-1.amazonaws.com
                '''
            }
        }

        stage('Push Image to Amazon ECR') {
            steps {
                sh '''
                docker tag $IMAGE_NAME:$IMAGE_TAG $ECR_REPO:$IMAGE_TAG
                docker push $ECR_REPO:$IMAGE_TAG
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
            echo 'Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}