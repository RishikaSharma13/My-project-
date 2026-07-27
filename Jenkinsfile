pipeline {
    agent any

    environment {
        IMAGE_NAME = "image-to-sketch"
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
    }

    post {
        success {
            echo "Docker image built successfully."
        }

        failure {
            echo "Pipeline failed."
        }
    }
}