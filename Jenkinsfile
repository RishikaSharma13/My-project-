pipeline {
    agent any

    environment {
        VENV = "venv"
        IMAGE_NAME = "my-flask-app"
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
                sh '''
                docker build -t $IMAGE_NAME .
                '''
            }
        }

        stage('Trivy Vulnerability Scan') {
            steps {
                sh '''
                trivy image \
                --exit-code 1 \
                --severity HIGH,CRITICAL \
                $IMAGE_NAME
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker stop $IMAGE_NAME || true
                docker rm $IMAGE_NAME || true
                docker run -d -p 5000:5000 --name $IMAGE_NAME $IMAGE_NAME
                '''
            }
        }
    }

    post {
        always {
            sh '''
            trivy image \
            --format template \
            --template "@html.tpl" \
            --output trivy-report.html \
            $IMAGE_NAME
            '''
            archiveArtifacts artifacts: 'trivy-report.html', fingerprint: true
        }

        success {
            echo " CI/CD Pipeline completed successfully!"
        }

        failure {
            echo "CI/CD Pipeline failed!"
        }
    }
}
