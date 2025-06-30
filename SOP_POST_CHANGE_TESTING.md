# Standard Operating Procedure (SOP): Post-Change Testing

## Overview
This SOP ensures that all major changes to the Market Voices system are properly tested before proceeding to production runs.

## When to Follow This SOP
- After dependency updates (`pip install`, `requirements.txt` changes)
- After code refactoring or major structural changes
- After configuration changes
- After security updates
- Before any production deployment
- After adding new features or modules

## Testing Sequence

### 1. Quick Test (REQUIRED)
**Command:** `python quick_test.py`

**Purpose:** Verify core functionality without running full production workflow
**Duration:** ~30 seconds
**What it tests:**
- ✅ Dependencies availability
- ✅ Module imports
- ✅ Configuration loading
- ✅ Security audit
- ✅ Logging configuration
- ✅ Host manager functionality
- ✅ Quality controller

**Expected Result:** All tests should pass (7/7)

### 2. Security Audit (REQUIRED)
**Command:** `python security_audit.py`

**Purpose:** Ensure no security issues were introduced
**Duration:** ~10 seconds
**What it tests:**
- ✅ File permissions
- ✅ Environment file security
- ✅ No secrets in logs
- ✅ Git tracking status

**Expected Result:** Security score 10/10

### 3. Unit Tests (RECOMMENDED)
**Command:** `pytest --maxfail=3 --disable-warnings -v`

**Purpose:** Run comprehensive test suite
**Duration:** ~5-10 minutes
**What it tests:**
- All unit tests
- Integration tests
- API connectivity tests

**Expected Result:** All tests pass

### 4. Dependency Audit (RECOMMENDED)
**Command:** `pip-audit`

**Purpose:** Check for known vulnerabilities
**Duration:** ~30 seconds
**Expected Result:** No vulnerabilities found

## Decision Matrix

| Quick Test | Security Audit | Unit Tests | Dependency Audit | Action |
|------------|----------------|------------|------------------|---------|
| ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | **PROCEED** to production |
| ✅ PASS | ✅ PASS | ✅ PASS | ⚠️ WARNINGS | **PROCEED** (review warnings) |
| ✅ PASS | ✅ PASS | ❌ FAIL | Any | **FIX** unit tests first |
| ✅ PASS | ❌ FAIL | Any | Any | **FIX** security issues first |
| ❌ FAIL | Any | Any | Any | **FIX** core functionality first |

## Failure Response

### Quick Test Failures
1. **Dependencies:** Check if all packages are installed correctly
2. **Imports:** Verify module structure and paths
3. **Configuration:** Check `.env` file and settings
4. **Security:** Review security configuration
5. **Logging:** Check logging setup
6. **Host Manager:** Verify host configuration
7. **Quality Controller:** Check quality validation logic

### Security Audit Failures
1. **File Permissions:** Run `chmod 600 .env`
2. **Git Tracking:** Ensure `.env` is in `.gitignore`
3. **Secrets in Logs:** Review logging configuration
4. **Output Directory:** Check directory permissions

### Unit Test Failures
1. Check test output for specific error messages
2. Verify API keys are valid
3. Check network connectivity
4. Review recent code changes

## Pre-Production Checklist

Before running a full production workflow, ensure:

- [ ] Quick test passes (7/7)
- [ ] Security audit passes (10/10)
- [ ] No critical unit test failures
- [ ] No high-severity dependency vulnerabilities
- [ ] All API keys are valid and accessible
- [ ] Environment variables are properly set
- [ ] Output directory has proper permissions

## Emergency Procedures

### If Quick Test Fails
1. **STOP** - Do not proceed to production
2. **DIAGNOSE** - Check error messages and logs
3. **FIX** - Address the specific failure
4. **RETEST** - Run quick test again
5. **DOCUMENT** - Note what was fixed

### If Production Run Fails After Passing Tests
1. **CHECK** - Review production logs
2. **ISOLATE** - Identify the specific failure point
3. **REVERT** - If necessary, revert to last known good state
4. **ANALYZE** - Determine why tests didn't catch the issue
5. **IMPROVE** - Update tests to catch similar issues

## Documentation

### Test Results Logging
- Save test results to `output/quick_test_results_YYYYMMDD_HHMMSS.txt`
- Include timestamp, test results, and any warnings
- Archive results for future reference

### Change Tracking
- Document all changes made
- Note which tests were run and their results
- Record any issues found and how they were resolved

## Maintenance

### Weekly Tasks
- Run full test suite
- Update dependencies if needed
- Review security audit results
- Clean up old test results

### Monthly Tasks
- Review and update this SOP
- Analyze test failure patterns
- Update test coverage if needed
- Review security best practices

---

**Last Updated:** 2025-06-29
**Version:** 1.0
**Next Review:** 2025-07-29 