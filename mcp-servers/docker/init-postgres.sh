#!/bin/bash
# 在 PostgreSQL 啟動時自動建立 Jira 和 BitBucket 各自的 database 和 user

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Jira 資料庫
    CREATE USER jira WITH PASSWORD 'jira1234';
    CREATE DATABASE jiradb
        WITH ENCODING='UNICODE'
        OWNER=jira
        CONNECTION LIMIT=-1;

    -- BitBucket 資料庫
    CREATE USER bitbucket WITH PASSWORD 'bitbucket1234';
    CREATE DATABASE bitbucketdb
        WITH ENCODING='UTF8'
        OWNER=bitbucket
        CONNECTION LIMIT=-1;
EOSQL

echo "✓ Jira 和 BitBucket 資料庫建立完成"
