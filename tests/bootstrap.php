<?php

declare(strict_types=1);

// Boots the real app config (DB, helpers, auth, api_auth) so admission tests exercise the same
// code path the live app runs — this project has no DB-mocking layer, and PersonAccessPolicy's
// canSeeL4() genuinely queries ref_role_capabilities, so tests run against the real local DB
// (same convention as tools/smoke_import_whitelist.php and the manual verification in scope.md).
require __DIR__ . '/../config/config.php'; // also require_once's vendor/autoload.php internally
