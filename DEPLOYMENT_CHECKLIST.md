# Production Deployment Checklist

## Pre-Deployment
- [ ] All required API keys configured in `.env`
- [ ] System validation passes: `python validate_production.py`
- [ ] Health check passes: `python main.py --health`
- [ ] Test mode works: `python main.py --test`
- [ ] Optional dependencies installed if needed: `pip install -r requirements-optional.txt`

## Production Deployment
- [ ] Run production deployment: `sudo python production_deploy.py`
- [ ] Environment variables configured securely
- [ ] Production directories created: `/etc/market-voices/`, `/var/log/market-voices/`
- [ ] File permissions set correctly (600 for .env, 644 for logs)
- [ ] Systemd service configured and enabled
- [ ] Log rotation configured

## Post-Deployment Validation
- [ ] Production script generation works: `python main.py`
- [ ] Cost monitoring active and reporting correctly
- [ ] Output files generated in correct location
- [ ] Log files created and accessible
- [ ] Health checks responding correctly

## Monitoring Setup
- [ ] API usage monitoring configured
- [ ] Cost alerts set up for budget thresholds
- [ ] System resource monitoring active
- [ ] Error alerting configured
- [ ] Daily summary reports being generated

## Security Checklist
- [ ] API keys stored securely (not in version control)
- [ ] File permissions properly restricted
- [ ] Log files don't contain sensitive information
- [ ] Network access properly configured
- [ ] Regular security audits scheduled

## Maintenance
- [ ] Log rotation configured to prevent disk space issues
- [ ] Regular backup of configuration files
- [ ] API key rotation schedule established
- [ ] System update procedures documented
- [ ] Incident response procedures documented
