pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "aggimallaabhishek/fluxsentinel-backend:latest"
    }

    stages {

        stage('Build Docker Image') {
            steps {
                sh 'docker buildx build --platform linux/amd64 -t $DOCKER_IMAGE ./backend'
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'USERNAME',
                    passwordVariable: 'PASSWORD'
                )]) {
                    sh 'echo $PASSWORD | docker login -u $USERNAME --password-stdin'
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                sh 'docker push $DOCKER_IMAGE'
            }
        }

        stage('Trigger Render Deploy') {
            steps {
                withCredentials([string(
                    credentialsId: 'render-deploy-hook',
                    variable: 'DEPLOY_HOOK'
                )]) {
                    sh 'curl -X POST $DEPLOY_HOOK'
                }
            }
        }
    }
}

