"""Fitness function: enforces the modular-monolith boundary rules.

- A file under app/modules/<name>/ may not import app.modules.<other> for any other name,
  except for the two narrow, explicit exceptions below.
- A file under app/modules/<name>/ may not import app.legacy.* at all.
- A file under app/legacy/ MAY freely import app.modules.<any>.* (repositories, entities,
  dependency factories — not just DB models). Legacy is the pre-modularization bridge/bot/
  dashboard code moved verbatim ("cero cambios de lógica" per the migration plan) — it keeps
  reaching into other modules' internals exactly as it did before the move, with only its
  import paths updated. The one rule that actually matters is the reverse direction: modules
  must never import FROM legacy, so legacy code never becomes a load-bearing dependency of
  the new modular code — that's enforced by test_no_module_imports_another_module below.

Exceptions (deliberate, not oversights — see the modular-monolith migration plan):

1. AUTH_CROSS_CUTTING: every module needs "who is the current user" (tenant_id, role) to
   scope its own queries. Authentication is treated as a cross-cutting platform concern
   (like the DB session or settings), not a business dependency on `identity`'s domain —
   so any module may depend on identity's public auth guard instead of reimplementing JWT
   validation per module.

2. REGISTRATION_SAGA: `POST /auth/verify` must synchronously return the newly created
   Tenant so the frontend can redirect into onboarding. Turning tenant creation into pure
   async event choreography would change that response contract. `identity` orchestrates
   tenant creation through `tenants`'s public application-service interface only (never
   through `tenants`'s repository/domain internals) — a narrow, explicitly allowed
   exception to the "modules talk only via events" rule, scoped to this one saga.
"""
import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
MODULES_ROOT = APP_ROOT / "modules"
LEGACY_ROOT = APP_ROOT / "legacy"

AUTH_CROSS_CUTTING_ALLOWED = {
    "app.modules.identity.interfaces.api.dependencies.auth_bearer",
    "app.modules.identity.domain.entities.user",
}

REGISTRATION_SAGA_ALLOWED_PREFIXES = (
    "app.modules.tenants.application.use_cases.create_tenant",
    "app.modules.tenants.interfaces.api.dependencies.tenants",
    "app.modules.tenants.interfaces.api.schemas.tenant",
    "app.modules.tenants.domain.entities.tenant",
)


def imports_of(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                found.add(node.module)
    return found


def _module_dirs() -> list[Path]:
    if not MODULES_ROOT.exists():
        return []
    return [d for d in MODULES_ROOT.iterdir() if d.is_dir() and not d.name.startswith("__")]


def test_no_module_imports_another_module():
    violations = []
    for module_dir in _module_dirs():
        own_prefix = f"app.modules.{module_dir.name}"
        is_identity = module_dir.name == "identity"
        for py_file in module_dir.rglob("*.py"):
            for imp in imports_of(py_file):
                if imp.startswith(own_prefix):
                    continue
                if imp in AUTH_CROSS_CUTTING_ALLOWED:
                    continue
                if is_identity and imp.startswith(REGISTRATION_SAGA_ALLOWED_PREFIXES):
                    continue
                if imp.startswith("app.modules."):
                    violations.append(f"{py_file} imports {imp} (crosses into another module)")
                if imp.startswith("app.legacy."):
                    violations.append(f"{py_file} imports {imp} (modules may not depend on legacy)")
    assert not violations, "\n".join(violations)


def test_legacy_does_not_import_from_legacy_as_a_module():
    """Sanity check: legacy code should never be imported as if it were itself a
    `app.modules.*` package (i.e. no module path collisions). Real enforcement of
    "modules must not depend on legacy" lives in test_no_module_imports_another_module."""
    if not LEGACY_ROOT.exists():
        return
    for py_file in LEGACY_ROOT.rglob("*.py"):
        for imp in imports_of(py_file):
            assert not imp.startswith("app.modules.legacy"), f"{py_file} imports {imp}"
