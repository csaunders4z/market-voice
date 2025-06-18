# Market Voices - Cloud Deployment & Dockerization

## ☁️ Cloud Hosting Strategy

- **Primary Platform:** AWS (Amazon Web Services)
- **Deployment Model:** Containerized (Docker)
- **Scalability:** Designed for auto-scaling and scheduled runs (e.g., after market close)
- **Availability:** 24/7, with monitoring and alerting

## 🐳 Dockerization

- **Why Docker?**
  - Ensures consistent environment across development, testing, and production
  - Simplifies dependency management
  - Enables easy deployment to any cloud provider

- **What's Included in the Docker Image?**
  - Python runtime and all dependencies (from `requirements.txt`)
  - All source code and scripts
  - Entrypoint for running daily workflow

- **Dockerfile Highlights:**
  - Multi-stage build for smaller images (optional)
  - `.env` file is mounted at runtime, not baked into the image
  - Output and logs are written to mounted volumes

## 🏗️ Deployment Architecture

- **AWS Service Options:**
  - **ECS (Elastic Container Service):** Run Docker containers on a managed cluster
  - **Fargate:** Serverless containers, no EC2 management
  - **Lambda (Container Image):** For short, scheduled jobs
  - **ECR (Elastic Container Registry):** Store Docker images
  - **S3:** Store output files, logs, and generated content
  - **CloudWatch:** Logging and monitoring

- **Typical Workflow:**
  1. Build Docker image locally or in CI
  2. Push image to AWS ECR
  3. Deploy container to ECS/Fargate/Lambda
  4. Schedule daily run (e.g., with EventBridge)
  5. Store outputs in S3, monitor with CloudWatch

## 🔄 CI/CD & Automation

- **Recommended Tools:**
  - **GitHub Actions** or **AWS CodePipeline** for automated builds and deployments
  - **Automated tests** run on every commit
  - **Secrets managed** via AWS Secrets Manager or SSM Parameter Store

## 🔐 Security & Secrets Management

- **Never bake API keys or secrets into Docker images**
- **Use environment variables** or AWS Secrets Manager for runtime secrets
- **Restrict IAM roles** to only necessary permissions

## 🚀 Example: Deploying to AWS Fargate

1. **Build and tag Docker image:**
   ```bash
   docker build -t market-voices:latest .
   docker tag market-voices:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/market-voices:latest
   ```
2. **Push to ECR:**
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
   docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/market-voices:latest
   ```
3. **Update ECS/Fargate service** to use the new image
4. **Schedule daily run** with EventBridge or ECS scheduled tasks

## 📋 Next Steps

- [ ] Finalize Dockerfile for production
- [ ] Set up AWS ECR and ECS/Fargate
- [ ] Configure CI/CD pipeline
- [ ] Document deployment process in detail
- [ ] Test end-to-end cloud deployment

---

**Last Updated:** June 17, 2025 