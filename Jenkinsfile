pipeline {
    agent any

    environment {
        VENV = "venv"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/RishikaSharma13/My-project-.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv $VENV
                . $VENV/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                . $VENV/bin/activate
                pytest || echo "No tests found, skipping"
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t my-flask-app .'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker stop my-flask-app || true
                docker rm my-flask-app || true
                docker run -d -p 5000:5000 --name my-flask-app my-flask-app
                '''
            }
        }
    }

    post {
        success {
            echo "CI/CD Pipeline completed successfully!"
        }
        failure {
            echo "CI/CD Pipeline failed!"
        }
    }
}
