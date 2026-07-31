pipeline {

    agent any

    options {
        timestamps()
    }

    environment {

        AWS_REGION = 'ap-south-1'

        IMAGE_NAME = 'image-to-sketch'

        ECR_REPO = '150619449649.dkr.ecr.ap-south-1.amazonaws.com/image-to-sketch'

        DEPLOY_PATH = '/opt/image-to-sketch'

        TRIVY_TEMPLATE = '/usr/local/share/trivy/templates/html.tpl'

        BUILD_IMAGE_TAG = "build-${BUILD_NUMBER}"

    }

    parameters {

        choice(
            name: 'ACTION',
            choices: ['Deploy', 'Rollback'],
            description: 'Choose the pipeline action.'
        )

        string(
            name: 'ROLLBACK_BUILD',
            defaultValue: '',
            description: 'Enter the build number to rollback (Example: 25)'
        )

        booleanParam(
            name: 'FAIL_ON_VULNERABILITIES',
            defaultValue: false,
            description: 'Fail pipeline if CRITICAL vulnerabilities are detected.'
        )

    }

    stages {

        stage('Checkout') {

            when {
                expression {
                    params.ACTION == 'Deploy'
                }
            }

            steps {
                checkout scm
            }

        }

        stage('Pipeline Configuration') {

            steps {

                script {

                    echo "===================================================="
                    echo "             PIPELINE CONFIGURATION"
                    echo "===================================================="
                    echo "Action                    : ${params.ACTION}"
                    echo "Build Tag                 : ${env.BUILD_IMAGE_TAG}"
                    echo "AWS Region                : ${env.AWS_REGION}"
                    echo "Fail On Vulnerabilities   : ${params.FAIL_ON_VULNERABILITIES}"
                    echo "===================================================="

                }

            }

        }

                stage('SonarQube Analysis') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                script {

                    echo "===================================================="
                    echo "Running SonarQube Analysis..."
                    echo "===================================================="

                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }

                }

            }

        }

        stage('Quality Gate') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                echo "Waiting for Quality Gate..."

                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }

                echo "Quality Gate Passed."

            }

        }

        stage('Build Docker Image') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Preparing Docker Build Cache..."
                echo "===================================================="

                docker pull $ECR_REPO:latest-dev || true

                echo ""
                echo "===================================================="
                echo "Building Docker Image..."
                echo "===================================================="

                docker buildx build \
                --builder jenkins-builder \
                --load \
                -t $IMAGE_NAME:$BUILD_IMAGE_TAG \
                .

                echo ""
                echo "Creating latest-dev tag..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $IMAGE_NAME:latest-dev

                echo ""
                echo "Available Images"

                docker images | grep $IMAGE_NAME
                '''

            }

        }

        stage('Trivy Image Scan') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                set -e

                mkdir -p reports

                echo "===================================================="
                echo "Running Trivy Security Scan..."
                echo "===================================================="

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
                echo "============== Scan Summary =============="

                cat reports/trivy-report.txt

                echo "=========================================="
                '''

            }

        }

        stage('Security Policy Check') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                script {

                    if (params.FAIL_ON_VULNERABILITIES) {

                        echo "Security Policy Enabled"

                        sh '''
                        trivy image \
                            --severity CRITICAL \
                            --exit-code 1 \
                            $IMAGE_NAME:$BUILD_IMAGE_TAG
                        '''

                    } else {

                        echo "Security Policy Disabled"

                    }

                }

            }

        }

        stage('Login to Amazon ECR') {

            when {
                expression {
                    params.ACTION == 'Deploy' ||
                    params.ACTION == 'Rollback'
                }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Logging into Amazon ECR..."
                echo "===================================================="

                aws ecr get-login-password \
                    --region $AWS_REGION | docker login \
                    --username AWS \
                    --password-stdin 150619449649.dkr.ecr.ap-south-1.amazonaws.com

                echo "Login Successful."
                '''

            }

        }

                stage('Push Image to Amazon ECR') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Pushing Immutable Image to Amazon ECR"
                echo "===================================================="

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $ECR_REPO:$BUILD_IMAGE_TAG

                docker push \
                    $ECR_REPO:$BUILD_IMAGE_TAG

                echo ""
                echo "Updating latest-dev tag..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $ECR_REPO:latest-dev

                docker push \
                    $ECR_REPO:latest-dev

                echo ""
                echo "Immutable Image : $BUILD_IMAGE_TAG"
                echo "Development Tag : latest-dev"

                echo "Images pushed successfully."
                '''

            }

        }

        stage('Deploy Development') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Deploying to Development Environment"
                echo "===================================================="

                cd $DEPLOY_PATH

                docker compose -f docker-compose.dev.yml down

                docker compose -f docker-compose.dev.yml pull

                docker compose -f docker-compose.dev.yml up -d --remove-orphans

                echo ""
                echo "Development deployment completed."
                '''

            }

        }

        stage('Health Check - Development') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                echo "Waiting for application to start..."

                sleep 10

                echo "Running Development Health Check..."

                curl -f http://localhost:4001/health

                echo ""
                echo "Development Health Check Passed."
                '''

            }

        }

        stage('Manual Approval') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                input(
                    message: 'Development deployment successful. Promote to Production?',
                    ok: 'Promote'
                )

            }

        }

        stage('Promote Image to Production') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Build Once, Promote Many"
                echo "===================================================="

                echo "Promoting immutable image..."

                docker tag \
                    $IMAGE_NAME:$BUILD_IMAGE_TAG \
                    $IMAGE_NAME:latest-prod

                docker tag \
                    $IMAGE_NAME:latest-prod \
                    $ECR_REPO:latest-prod

                docker push \
                    $ECR_REPO:latest-prod

                echo ""
                echo "Production Tag : latest-prod"
                echo "Promotion completed successfully."
                '''

            }

        }

        stage('Deploy Production') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Deploying to Production"
                echo "===================================================="

                cd $DEPLOY_PATH

                docker compose -f docker-compose.prod.yml down

                docker compose -f docker-compose.prod.yml pull

                docker compose -f docker-compose.prod.yml up -d --remove-orphans

                docker image prune -f

                echo ""
                echo "Production deployment completed."
                '''

            }

        }

        stage('Health Check - Production') {

            when {
                expression { params.ACTION == 'Deploy' }
            }

            steps {

                sh '''
                echo "Waiting for Production application..."

                sleep 10

                echo "Running Production Health Check..."

                curl -f http://localhost:4000/health

                echo ""
                echo "Production Health Check Passed."
                '''

            }

        }

                stage('Rollback Production') {

            when {
                expression { params.ACTION == 'Rollback' }
            }

            steps {

                sh '''
                set -e

                echo "===================================================="
                echo "Production Rollback"
                echo "===================================================="

                if [ -z "$ROLLBACK_BUILD" ]; then
                    echo "ERROR: Rollback build number is required."
                    exit 1
                fi

                echo ""
                echo "Rolling back to build-${ROLLBACK_BUILD}"
                echo ""

                docker pull $ECR_REPO:build-$ROLLBACK_BUILD

                docker tag \
                    $ECR_REPO:build-$ROLLBACK_BUILD \
                    $ECR_REPO:latest-prod

                docker push $ECR_REPO:latest-prod

                cd $DEPLOY_PATH

                docker compose -f docker-compose.prod.yml down

                docker compose -f docker-compose.prod.yml pull

                docker compose -f docker-compose.prod.yml up -d --remove-orphans

                echo ""
                echo "Rollback deployment completed."
                '''

            }

        }

        stage('Health Check - Rollback') {

            when {
                expression { params.ACTION == 'Rollback' }
            }

            steps {

                sh '''
                echo "Waiting for Production application..."

                sleep 10

                echo "Running Production Health Check..."

                curl -f http://localhost:4000/health

                echo ""
                echo "Rollback Health Check Passed."
                '''

            }

        }

    }

    post {

        always {

            echo "===================================================="
            echo "Archiving Reports..."
            echo "===================================================="

            archiveArtifacts(
                artifacts: 'reports/*',
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo "Cleaning Jenkins Workspace..."

            deleteDir()

        }

        success {

            echo ""
            echo "===================================================="
            echo "Pipeline completed successfully."
            echo "===================================================="

        }

        failure {

            echo ""
            echo "===================================================="
            echo "Pipeline failed."
            echo "Please check the failed stage and console logs."
            echo "===================================================="

        }

    }

}