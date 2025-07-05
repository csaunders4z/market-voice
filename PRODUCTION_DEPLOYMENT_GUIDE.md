# Market Voices - Production Deployment Guide

## 🚨 **CRITICAL: API Key Management for Production**

### **The Problem**
The current TODO list mentions "Add Real API Keys and Deploy" but there's a fundamental architecture issue:
- The system was designed to load API keys from a local `.env` file
- In production/cloud environments, there's no local `.env` file
- Background agents and cloud services can't access your local machine's `.env` file

### **The Solution: Cloud-Native Environment Variables**

## 🏗️ **Cloud Deployment Options**

### **Option 1: AWS ECS/Fargate (Recommended)**

#### **Step 1: Prepare Environment Variables**
Instead of using a `.env` file, set environment variables directly in your cloud environment:

```bash
# Required API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
NEWS_API_KEY=your_news_api_key
OPENAI_API_KEY=your_openai_key
FMP_API_KEY=your_fmp_key
BIZTOC_API_KEY=your_biztoc_key
NEWSDATA_IO_API_KEY=your_newsdata_key
THE_NEWS_API_API_KEY=your_the_news_api_key

# Optional Settings
TEST_MODE=0
LOG_LEVEL=INFO
TARGET_RUNTIME_MINUTES=12
```

#### **Step 2: AWS ECS Task Definition**
```json
{
  "family": "market-voices",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "market-voices",
      "image": "your-account.dkr.ecr.region.amazonaws.com/market-voices:latest",
      "environment": [
        {"name": "ALPHA_VANTAGE_API_KEY", "value": "your_key"},
        {"name": "NEWS_API_KEY", "value": "your_key"},
        {"name": "OPENAI_API_KEY", "value": "your_key"},
        {"name": "FMP_API_KEY", "value": "your_key"},
        {"name": "TEST_MODE", "value": "0"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/market-voices",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### **Step 3: AWS Secrets Manager (More Secure)**
For better security, use AWS Secrets Manager:

```json
{
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:market-voices/openai:api_key::"
    },
    {
      "name": "NEWS_API_KEY", 
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:market-voices/news:api_key::"
    }
  ]
}
```

### **Option 2: GitHub Actions (CI/CD)**

#### **Step 1: Set Repository Secrets**
In your GitHub repository settings, add secrets:
- `ALPHA_VANTAGE_API_KEY`
- `NEWS_API_KEY`
- `OPENAI_API_KEY`
- `FMP_API_KEY`

#### **Step 2: GitHub Actions Workflow**
```yaml
name: Deploy Market Voices

on:
  schedule:
    - cron: '0 21 * * 1-5'  # 9 PM UTC, Mon-Fri (after market close)
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run Market Voices
        env:
          ALPHA_VANTAGE_API_KEY: ${{ secrets.ALPHA_VANTAGE_API_KEY }}
          NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          FMP_API_KEY: ${{ secrets.FMP_API_KEY }}
          BIZTOC_API_KEY: ${{ secrets.BIZTOC_API_KEY }}
          TEST_MODE: 0
          LOG_LEVEL: INFO
        run: |
          python main.py
      
      - name: Upload outputs
        uses: actions/upload-artifact@v3
        with:
          name: market-voices-output
          path: output/
```

### **Option 3: Google Cloud Run**

#### **Step 1: Deploy with Environment Variables**
```bash
gcloud run deploy market-voices \
  --image gcr.io/YOUR-PROJECT/market-voices \
  --platform managed \
  --region us-central1 \
  --set-env-vars ALPHA_VANTAGE_API_KEY=your_key,NEWS_API_KEY=your_key,OPENAI_API_KEY=your_key,TEST_MODE=0
```

#### **Step 2: Use Cloud Scheduler**
```bash
gcloud scheduler jobs create http market-voices-daily \
  --schedule="0 21 * * 1-5" \
  --uri=https://market-voices-xxxxx-uc.a.run.app \
  --http-method=POST
```

## 🔐 **Security Best Practices**

### **1. Never Hardcode API Keys**
```python
# ❌ NEVER DO THIS
api_key = "sk-1234567890abcdef"

# ✅ DO THIS
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")
```

### **2. Use Secrets Management**
- **AWS**: Secrets Manager or Systems Manager Parameter Store
- **GCP**: Secret Manager
- **Azure**: Key Vault
- **GitHub**: Repository Secrets

### **3. Environment-Specific Configuration**
```python
# Different configs for different environments
if os.getenv("ENVIRONMENT") == "production":
    LOG_LEVEL = "WARNING"
    TEST_MODE = False
elif os.getenv("ENVIRONMENT") == "staging":
    LOG_LEVEL = "INFO"
    TEST_MODE = True
else:
    LOG_LEVEL = "DEBUG"
    TEST_MODE = True
```

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] **API Keys Obtained**: Get production API keys for all services
- [ ] **Environment Variables Set**: Configure all required environment variables
- [ ] **Security Audit**: Run security audit to ensure no hardcoded secrets
- [ ] **Performance Testing**: Test with full production load
- [ ] **Cost Estimation**: Calculate expected API costs

### **Deployment**
- [ ] **Cloud Environment Setup**: ECS/Fargate, Cloud Run, or GitHub Actions
- [ ] **Environment Variables**: Set all API keys as environment variables
- [ ] **Monitoring**: Set up CloudWatch, Stackdriver, or equivalent
- [ ] **Alerting**: Configure alerts for failures and high costs
- [ ] **Scheduling**: Set up daily execution schedule

### **Post-Deployment**
- [ ] **Smoke Test**: Run manual test to verify deployment
- [ ] **Monitor Logs**: Check logs for errors or warnings
- [ ] **Validate Output**: Ensure generated content meets quality standards
- [ ] **Cost Monitoring**: Track API usage and costs
- [ ] **Performance Monitoring**: Monitor execution times and resource usage

## 💰 **Cost Management**

### **Estimated Monthly Costs (Production)**
- **OpenAI GPT-4**: $50-100/month (depends on script length)
- **News API**: $0-50/month (depends on volume)
- **Alpha Vantage**: $0-25/month (free tier may suffice)
- **FMP**: $0-30/month (depends on usage)
- **Cloud Infrastructure**: $20-50/month (ECS/Fargate)

**Total Estimated**: $100-255/month

### **Cost Optimization Strategies**
1. **Caching**: Cache API responses to reduce redundant calls
2. **Batch Processing**: Process multiple symbols in single API calls
3. **Off-Peak Scheduling**: Run during off-peak hours for lower costs
4. **Rate Limiting**: Implement intelligent rate limiting
5. **Monitoring**: Set up cost alerts and usage monitoring

## 🚀 **Quick Start: GitHub Actions Deployment**

This is the **easiest way to get started** with production deployment:

### **Step 1: Fork the Repository**
Fork the Market Voices repository to your GitHub account.

### **Step 2: Add Secrets**
In your forked repository, go to Settings → Secrets and Variables → Actions, and add:
- `ALPHA_VANTAGE_API_KEY`
- `NEWS_API_KEY`
- `OPENAI_API_KEY`
- `FMP_API_KEY`
- `BIZTOC_API_KEY`

### **Step 3: Enable Actions**
Create `.github/workflows/deploy.yml` with the workflow above.

### **Step 4: Test**
Trigger the workflow manually to test, then let it run on schedule.

## 🆘 **Troubleshooting**

### **Common Issues**

#### **"API Key not found" errors**
- **Cause**: Environment variables not set correctly
- **Solution**: Verify environment variable names match exactly

#### **"Permission denied" errors**
- **Cause**: Cloud service lacks permissions
- **Solution**: Ensure service has proper IAM roles

#### **High API costs**
- **Cause**: Too many API calls or premium endpoints
- **Solution**: Implement caching and rate limiting

#### **Deployment failures**
- **Cause**: Missing dependencies or configuration
- **Solution**: Check logs and verify all requirements are met

---

## 📞 **Support**

For deployment issues:
1. Check the logs first
2. Verify all environment variables are set
3. Ensure API keys are valid and have sufficient credits
4. Review the security audit results

---

*Ready to deploy? Start with GitHub Actions - it's the quickest path to production!*