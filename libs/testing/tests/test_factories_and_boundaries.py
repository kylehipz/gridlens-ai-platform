import ast
from pathlib import Path
import unittest

from gridlens_testing import make_tenant, make_user

ROOT = Path(__file__).resolve().parents[3]
PRODUCT_IMPORT_PREFIXES = ("services", "workers", "frontend")
PRODUCT_MODULE_WORDS = ("ingestion", "evaluation", "reporting", "assistant")


class TestingLibraryTests(unittest.TestCase):
    def test_factories_create_deterministic_tenant_user_membership_data(self):
        tenant_a = make_tenant("tenant_a")
        tenant_b = make_tenant("tenant_b")
        user_a = make_user("analyst", tenant_a, role="Analyst")
        user_b = make_user("viewer", tenant_b, role="Viewer")
        self.assertNotEqual(tenant_a.id, tenant_b.id)
        self.assertEqual("tenant_a_id", user_a.tenant_id)
        self.assertEqual("active", user_b.membership_status)

    def test_shared_libraries_do_not_import_product_modules(self):
        violations = []
        for path in (ROOT / "libs").glob("*/src/**/*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    module = node.names[0].name
                if not module:
                    continue
                first = module.split(".", 1)[0]
                if first in PRODUCT_IMPORT_PREFIXES or any(word in module for word in PRODUCT_MODULE_WORDS):
                    violations.append(f"{path.relative_to(ROOT)} imports {module}")
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
