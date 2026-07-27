pipeline {
    agent any

    environment {
        IMAGE_NAME = "image-to-sketch"
        AWS_REGION = "ap-south-1"
        ECR_REPO = "150619449649.dkr.ecr.ap-south-1.amazonaws.com/image-to-sketch"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/RishikaSharma13/My-project-.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t $IMAGE_NAME .
                '''
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
        success {
            echo 'Pipeline v2 completed successfully!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}