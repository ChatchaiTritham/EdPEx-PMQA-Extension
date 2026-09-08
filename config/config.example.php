<?php
// Example environment-variable-driven DB config, matching this project's
// convention (see the parent repository's config/config.php). Copy to
// config.php and set real values, or export these as actual environment
// variables before running the test suite. No real credentials are stored
// in this repository.

putenv('APP_DB_HOST=127.0.0.1');
putenv('APP_DB_NAME=your_database_name');
putenv('APP_DB_USER=your_db_user');
putenv('APP_DB_PASS=your_db_password');
