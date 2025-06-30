#!/usr/bin/env python3
"""
Security Audit Script for Market Voices
Run this script to perform a comprehensive security audit
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.security import security_config
from loguru import logger


def main():
    """Run comprehensive security audit"""
    print("🔒 MARKET VOICES SECURITY AUDIT")
    print("=" * 50)
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{message}")
    
    # Run security audit
    audit_results = security_config.run_security_audit()
    
    # Display results
    print("\n📋 AUDIT RESULTS:")
    print("-" * 30)
    
    # File permissions
    perms = audit_results['file_permissions']
    print(f"🔐 .env file secure: {'✅' if perms['env_file_secure'] else '❌'}")
    print(f"📁 Output directories secure: {'✅' if perms['output_dirs_secure'] else '❌'}")
    print(f"📝 No secrets in logs: {'✅' if perms['no_secrets_in_logs'] else '❌'}")
    
    # Environment file status
    print(f"📄 .env file exists: {'✅' if audit_results['env_file_exists'] else '❌'}")
    print(f"🚫 .env tracked by git: {'❌ CRITICAL' if audit_results['env_file_tracked'] else '✅'}")
    
    # Recommendations
    if audit_results['recommendations']:
        print("\n⚠️  RECOMMENDATIONS:")
        print("-" * 20)
        for i, rec in enumerate(audit_results['recommendations'], 1):
            print(f"{i}. {rec}")
    else:
        print("\n✅ No security issues found!")
    
    # Security score
    issues = len(audit_results['recommendations'])
    if issues == 0:
        score = 10
    elif issues <= 2:
        score = 8
    elif issues <= 4:
        score = 6
    else:
        score = 4
    
    print(f"\n🏆 SECURITY SCORE: {score}/10")
    
    # Save audit results
    output_file = Path("output") / "security_audit.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)
    
    print(f"\n📊 Audit results saved to: {output_file}")
    
    # Return appropriate exit code
    if issues == 0:
        print("\n🎉 All security checks passed!")
        return 0
    else:
        print(f"\n⚠️  {issues} security issue(s) found. Please review recommendations.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 