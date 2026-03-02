pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  parameters {
    booleanParam(name: 'TRIGGER_RENDER_DEPLOY', defaultValue: false, description: 'Trigger Render deploy hook after pushing Docker image')
  }

  environment {
    IMAGE_REPO = 'docker.io/aggimallaabhishek/fluxsentinel-backend'
    IMAGE_TAG = "${BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Docker Access Check') {
      steps {
        sh 'docker version'
      }
    }

    stage('Build Backend Image') {
      steps {
        sh 'docker build -t ${IMAGE_REPO}:${IMAGE_TAG} -t ${IMAGE_REPO}:latest ./backend'
      }
    }

    stage('Run Backend Tests In Container') {
      steps {
        sh 'docker run --rm ${IMAGE_REPO}:${IMAGE_TAG} pytest -q'
      }
    }

    stage('Push Docker Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh '''
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
            docker push ${IMAGE_REPO}:${IMAGE_TAG}
            docker push ${IMAGE_REPO}:latest
          '''
        }
      }
    }

    stage('Trigger Render Deploy Hook') {
      when {
        expression { return params.TRIGGER_RENDER_DEPLOY }
      }
      steps {
        withCredentials([string(credentialsId: 'render-deploy-hook', variable: 'RENDER_DEPLOY_HOOK_URL')]) {
          sh 'curl -fsS -X POST "$RENDER_DEPLOY_HOOK_URL"'
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
      cleanWs()
    }
  }
}
