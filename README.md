# Suno Music Scraper
A scraper for Suno.com that creates and downloads songs using AWS (Fargate & ECR for scraping and S3 for storing Chrome profiles) and Twilio for Suno authentication and Supabase for storing songs and updating records (e.g outstanding credits on all Suno accounts you use, song data). 

## Prerequisites

Before you begin, ensure you have the following installed on your machine:
- [Docker](https://docs.docker.com/engine/install/)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

## AWS ECR & Fargate Deployment Guide

Follow these steps to deploy the scraper to AWS Fargate:

### 1. Create an ECR Repository

```bash
aws ecr create-repository --repository-name suno-music-scraper
```

### 2. Authenticate with ECR

```bash
aws ecr get-login-password --region your-region-here | docker login --username AWS --password-stdin aws-account-id.dkr.ecr.your-region-here.amazonaws.com
```

### 3. Build and Tag the Docker Image

```bash
docker build -t suno-music-scraper .
docker tag suno-music-scraper:latest aws-account-id.dkr.ecr.your-region-here.amazonaws.com/suno-music-scraper:latest
```

### 4. Push the Image to ECR

```bash
docker push aws-account-id.dkr.ecr.your-region-here.amazonaws.com/suno-music-scraper:latest
```

### 5. Deploy to Fargate

Update `Parameters.ContainerImage.Default` in `fargate-docker-scraper.yaml` or use the following command:

```bash
aws cloudformation deploy \
    --template-file fargate-suno-scraper.yaml \
    --stack-name fargate-suno-scraper \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        ContainerImage="aws-account-id.dkr.ecr.your-region-here.amazonaws.com/suno-music-scraper:latest" \
        ContainerPort=80 \
        TaskCpu=2048 \
        TaskMemory=4096
```

## Maintenance and Updates

### Updating the Fargate Deployment

To update your Fargate setup:

1. Create a changeset:
```bash
aws cloudformation create-change-set --stack-name fargate-suno-scraper --template-body file://fargate-suno-scraper.yaml --change-set-name my-change-set --capabilities CAPABILITY_NAMED_IAM
```

2. Review the changes:
```bash
aws cloudformation describe-change-set --change-set-name my-change-set --stack-name fargate-suno-scraper
```

3. Execute the changeset:
```bash
aws cloudformation execute-change-set --change-set-name my-change-set --stack-name fargate-suno-scraper
```

### Updating the ECR Deployment

To deploy code changes to ECR:

```bash
docker build -t suno-music-scraper .
docker tag suno-music-scraper:latest aws-account-id.dkr.ecr.your-region-here.amazonaws.com/suno-music-scraper:latest
docker push aws-account-id.dkr.ecr.your-region-here.amazonaws.com/suno-music-scraper:latest
```

## Cleanup

### Deleting the Stack

To remove the entire CloudFormation stack:

```bash
aws cloudformation delete-stack --stack-name fargate-suno-scraper
```

Check the deletion status:

```bash
aws cloudformation describe-stacks --stack-name fargate-suno-scraper
```
