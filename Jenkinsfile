pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'FAIL_ON_VULNERABILITIES',
            defaultValue: false,
            description: 'Fail the pipeline if CRITICAL vulnerabilities are found'
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
                docker build -t $IMAGE_NAME .
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                echo "========================================="
                echo "Running Trivy Security Scan..."
                echo "========================================="

                # Generate Text Report
                trivy image \
                  --severity HIGH,CRITICAL \
                  --format table \
                  --output trivy-report.txt \
                  $IMAGE_NAME:latest

                # Generate HTML Report
                trivy image \
                  --severity HIGH,CRITICAL \
                  --format template \
                  --template "@${TRIVY_TEMPLATE}" \
                  --output trivy-report.html \
                  $IMAGE_NAME:latest

                echo ""
                echo "========== Trivy Scan Summary =========="
                cat trivy-report.txt
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
                          $IMAGE_NAME:latest
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
                docker tag $IMAGE_NAME:latest $ECR_REPO:latest
                docker push $ECR_REPO:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                cd /opt/image-to-sketch

                docker compose pull

                docker compose down

                docker compose up -d --remove-orphans

                docker image prune -f
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                sleep 10

                curl -f http://localhost:4000/health
                '''
            }
        }
    }

    post {

        always {
            archiveArtifacts artifacts: 'trivy-report.txt, trivy-report.html', fingerprint: true
        }

        success {
            echo 'Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}