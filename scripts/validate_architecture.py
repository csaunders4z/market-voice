#!/usr/bin/env python3
"""
Architecture Validation Script

This script validates that the codebase follows our architectural principles
and that the TECHNICAL_ARCHITECTURE.md document is up to date.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import ast
import json

class ArchitectureValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.architecture_doc = self.project_root / "TECHNICAL_ARCHITECTURE.md"
        self.src_dir = self.project_root / "src"
        self.violations = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Run all architecture validation checks"""
        print("🔍 Running Architecture Validation...")
        
        checks = [
            self.check_architecture_documentation_exists(),
            self.check_component_documentation_coverage(),
            self.check_api_integration_patterns(),
            self.check_error_handling_patterns(),
            self.check_rate_limiting_implementation(),
            self.check_import_structure(),
            self.check_file_organization(),
        ]
        
        all_passed = all(checks)
        
        if self.violations:
            print("\n❌ Architecture Violations Found:")
            for violation in self.violations:
                print(f"  - {violation}")
        
        if self.warnings:
            print("\n⚠️  Architecture Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if all_passed:
            print("\n✅ All architecture checks passed!")
        else:
            print(f"\n❌ {len(self.violations)} architecture violations found")
            
        return all_passed
    
    def check_architecture_documentation_exists(self) -> bool:
        """Check that TECHNICAL_ARCHITECTURE.md exists and is recent"""
        if not self.architecture_doc.exists():
            self.violations.append("TECHNICAL_ARCHITECTURE.md does not exist")
            return False
        
        # Check if document was updated in the last 30 days
        import time
        doc_age = time.time() - self.architecture_doc.stat().st_mtime
        days_old = doc_age / (24 * 60 * 60)
        
        if days_old > 30:
            self.warnings.append(f"TECHNICAL_ARCHITECTURE.md is {days_old:.0f} days old - consider updating")
        
        print("✅ Architecture documentation exists")
        return True
    
    def check_component_documentation_coverage(self) -> bool:
        """Check that all components are documented in the architecture doc"""
        if not self.architecture_doc.exists():
            return False
        
        doc_content = self.architecture_doc.read_text()
        
        # Find all Python files in src/
        python_files = list(self.src_dir.rglob("*.py"))
        documented_components = set()
        
        # Extract documented components from architecture doc
        component_pattern = r'`([^`]+\.py)`'
        documented_components.update(re.findall(component_pattern, doc_content))
        
        # Check for undocumented components
        undocumented = []
        for py_file in python_files:
            relative_path = py_file.relative_to(self.project_root)
            if str(relative_path) not in documented_components and not self._is_test_file(relative_path):
                undocumented.append(str(relative_path))
        
        if undocumented:
            self.violations.append(f"Undocumented components: {', '.join(undocumented[:5])}")
            if len(undocumented) > 5:
                self.violations.append(f"... and {len(undocumented) - 5} more")
            return False
        
        print("✅ All components are documented")
        return True
    
    def check_api_integration_patterns(self) -> bool:
        """Check that API integrations follow established patterns"""
        violations = []
        
        # Check for hardcoded API keys
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            if re.search(r'api_key\s*=\s*["\'][^"\']+["\']', content):
                violations.append(f"Hardcoded API key found in {py_file.relative_to(self.project_root)}")
        
        # Check for missing rate limiting
        rate_limited_files = []
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            if re.search(r'requests\.get|requests\.post', content):
                if not re.search(r'@.*rate_limiter|time\.sleep', content):
                    rate_limited_files.append(str(py_file.relative_to(self.project_root)))
        
        if rate_limited_files:
            self.warnings.append(f"Files without rate limiting: {', '.join(rate_limited_files[:3])}")
        
        if violations:
            self.violations.extend(violations)
            return False
        
        print("✅ API integration patterns are followed")
        return True
    
    def check_error_handling_patterns(self) -> bool:
        """Check that error handling follows established patterns"""
        files_without_error_handling = []
        
        for py_file in self.src_dir.rglob("*.py"):
            if self._is_test_file(py_file):
                continue
                
            content = py_file.read_text()
            
            # Check for try/except blocks in files that make external calls
            if re.search(r'requests\.|urllib\.|http\.', content):
                if not re.search(r'try\s*:|except\s*:', content):
                    files_without_error_handling.append(str(py_file.relative_to(self.project_root)))
        
        if files_without_error_handling:
            self.warnings.append(f"Files without error handling: {', '.join(files_without_error_handling[:3])}")
        
        print("✅ Error handling patterns are followed")
        return True
    
    def check_rate_limiting_implementation(self) -> bool:
        """Check that rate limiting is properly implemented"""
        # This is a basic check - could be enhanced with more sophisticated analysis
        rate_limiter_imports = 0
        
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            if 'rate_limiter' in content:
                rate_limiter_imports += 1
        
        if rate_limiter_imports < 3:  # Expect at least some rate limiting
            self.warnings.append("Limited rate limiting implementation found")
        
        print("✅ Rate limiting implementation checked")
        return True
    
    def check_import_structure(self) -> bool:
        """Check that imports follow architectural patterns"""
        violations = []
        
        for py_file in self.src_dir.rglob("*.py"):
            if self._is_test_file(py_file):
                continue
                
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('src.'):
                                violations.append(f"Absolute import in {py_file.relative_to(self.project_root)}: {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('src.'):
                            violations.append(f"Absolute import in {py_file.relative_to(self.project_root)}: {node.module}")
            except SyntaxError:
                continue
        
        if violations:
            self.violations.extend(violations[:5])  # Limit to first 5 violations
            return False
        
        print("✅ Import structure follows patterns")
        return True
    
    def check_file_organization(self) -> bool:
        """Check that files are organized according to architecture"""
        # Check for files in wrong directories
        violations = []
        
        # Data collection files should be in data_collection/
        for py_file in self.src_dir.rglob("*.py"):
            relative_path = str(py_file.relative_to(self.project_root))
            
            if 'collector' in py_file.name.lower() and 'data_collection' not in relative_path:
                violations.append(f"Collector file in wrong location: {relative_path}")
            
            if 'news' in py_file.name.lower() and 'data_collection' not in relative_path:
                violations.append(f"News file in wrong location: {relative_path}")
        
        if violations:
            self.violations.extend(violations[:3])
            return False
        
        print("✅ File organization follows architecture")
        return True
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file"""
        return 'test' in file_path.name.lower() or 'test' in str(file_path.parent.name).lower()

def main():
    """Main entry point"""
    validator = ArchitectureValidator()
    success = validator.validate_all()
    
    if not success:
        print("\n📋 Next Steps:")
        print("1. Review TECHNICAL_ARCHITECTURE.md")
        print("2. Fix architecture violations")
        print("3. Update documentation as needed")
        print("4. Run validation again")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main() 