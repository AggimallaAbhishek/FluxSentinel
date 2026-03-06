pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  parameters {
    booleanParam(
      name: 'PUSH_DOCKER_IMAGE',
      defaultValue: false,
      description: 'Push built backend image to Docker Hub (Render service currently deploys from source).'
    )
    booleanParam(
      name: 'TRIGGER_RENDER_DEPLOY',
      defaultValue: true,
      description: 'Trigger Render deploy hook after tests pass.'
    )
  }

  environment {
    IMAGE_REPO = 'docker.io/aggimallaabhishek/fluxsentinel-backend'
    IMAGE_TAG = "${BUILD_NUMBER}"
    IMAGE_LATEST = "${IMAGE_REPO}:latest"
    IMAGE_VERSION = "${IMAGE_REPO}:${IMAGE_TAG}"
  }

  stages {
    stage('Checkout SCM') {
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
        sh 'docker build --platform linux/amd64 -t ${IMAGE_VERSION} -t ${IMAGE_LATEST} ./backend'
      }
    }

    stage('Run Backend Tests In Container') {
      steps {
        sh 'docker run --rm ${IMAGE_VERSION} pytest -q'
      }
    }

    stage('Push Docker Image') {
      when {
        expression { return params.PUSH_DOCKER_IMAGE }
      }
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'dockerhub-creds',
          usernameVariable: 'DOCKER_USER',
          passwordVariable: 'DOCKER_PASS'
        )]) {
          sh '''
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
            docker push ${IMAGE_VERSION}
            docker push ${IMAGE_LATEST}
          '''
        }
      }
    }

    stage('Trigger Render Deploy Hook') {
      when {
        expression { return params.TRIGGER_RENDER_DEPLOY }
      }
      steps {
        withCredentials([string(
          credentialsId: 'render-deploy-hook',
          variable: 'RENDER_DEPLOY_HOOK_URL'
        )]) {
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
