FROM jenkins/jenkins:lts-jdk17

USER root

# Install Docker CLI so Jenkins pipeline can run docker build/push commands.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

USER jenkins
