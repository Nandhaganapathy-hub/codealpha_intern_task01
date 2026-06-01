-- ============================================================
-- DATA REDUNDANCY REMOVAL SYSTEM - DATABASE SCHEMA
-- File: database/schema.sql
-- Purpose: Creates all tables for the system
-- ============================================================

-- Step 1: Create and use the database
CREATE DATABASE IF NOT EXISTS data_redundancy_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE data_redundancy_db;

-- ============================================================
-- TABLE: records
-- Purpose: Stores only UNIQUE, verified records
-- This is the MASTER table — no duplicates allowed here
-- ============================================================
CREATE TABLE IF NOT EXISTS records (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    unique_id       VARCHAR(100) NOT NULL UNIQUE,   -- Unique identifier (e.g., employee ID, customer ID)
    full_name       VARCHAR(255) NOT NULL,            -- Full name of the person
    email           VARCHAR(255) NOT NULL UNIQUE,    -- Email must be unique
    phone           VARCHAR(20)  NOT NULL UNIQUE,    -- Phone must be unique
    address         TEXT,                             -- Physical address
    city            VARCHAR(100),                    -- City name
    state           VARCHAR(100),                    -- State/Province
    country         VARCHAR(100) DEFAULT 'India',    -- Country
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- When it was first added
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- Last update time
);

-- ============================================================
-- TABLE: submission_log
-- Purpose: Logs EVERY submission attempt with its result
-- Tracks: UNIQUE, REDUNDANT (duplicate), or FALSE_POSITIVE
-- ============================================================
CREATE TABLE IF NOT EXISTS submission_log (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    submitted_uid   VARCHAR(100),                    -- Submitted unique_id
    submitted_name  VARCHAR(255),                    -- Submitted name
    submitted_email VARCHAR(255),                    -- Submitted email
    submitted_phone VARCHAR(20),                     -- Submitted phone
    submitted_addr  TEXT,                            -- Submitted address
    classification  ENUM('UNIQUE','REDUNDANT','FALSE_POSITIVE') NOT NULL,  -- Result
    match_reason    TEXT,                            -- Why it was classified this way
    similarity_score FLOAT DEFAULT 0.0,             -- How similar it is (0-100%)
    matched_record_id INT,                           -- Which master record it matched (if any)
    submitted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (matched_record_id) REFERENCES records(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: duplicate_pairs
-- Purpose: Stores pairs of records that are similar (false positives)
-- Helps analysts review potential duplicates manually
-- ============================================================
CREATE TABLE IF NOT EXISTS duplicate_pairs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    record_id_1     INT NOT NULL,
    record_id_2     INT NOT NULL,
    similarity_score FLOAT NOT NULL,               -- Combined similarity percentage
    name_score      FLOAT DEFAULT 0.0,             -- Name similarity score
    address_score   FLOAT DEFAULT 0.0,             -- Address similarity score
    status          ENUM('PENDING','CONFIRMED','DISMISSED') DEFAULT 'PENDING',
    detected_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (record_id_1) REFERENCES records(id) ON DELETE CASCADE,
    FOREIGN KEY (record_id_2) REFERENCES records(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: dashboard_stats (Cache Table)
-- Purpose: Caches dashboard numbers so we don't recalculate every time
-- ============================================================
CREATE TABLE IF NOT EXISTS dashboard_stats (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    stat_key        VARCHAR(100) UNIQUE NOT NULL,   -- e.g., 'total_unique', 'total_redundant'
    stat_value      INT DEFAULT 0,
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES: Speed up search queries significantly
-- ============================================================
CREATE INDEX idx_email    ON records(email);
CREATE INDEX idx_phone    ON records(phone);
CREATE INDEX idx_uid      ON records(unique_id);
CREATE INDEX idx_city     ON records(city);
CREATE INDEX idx_log_class ON submission_log(classification);

-- ============================================================
-- SEED: Initialize dashboard statistics counters
-- ============================================================
INSERT INTO dashboard_stats (stat_key, stat_value) VALUES
('total_records',   0),
('total_unique',    0),
('total_redundant', 0),
('total_false_pos', 0)
ON DUPLICATE KEY UPDATE stat_value = stat_value;

-- ============================================================
-- SEED: Sample unique records for testing
-- ============================================================
INSERT INTO records (unique_id, full_name, email, phone, address, city, state, country) VALUES
('EMP001', 'Aarav Sharma',     'aarav.sharma@email.com',    '9876543210', '12 MG Road',          'Mumbai',   'Maharashtra', 'India'),
('EMP002', 'Priya Nair',       'priya.nair@email.com',      '9123456780', '45 Anna Salai',        'Chennai',  'Tamil Nadu',  'India'),
('EMP003', 'Rohan Mehta',      'rohan.mehta@email.com',     '9988776655', '78 Sector 21',         'Noida',    'UP',          'India'),
('EMP004', 'Kavitha Reddy',    'kavitha.reddy@email.com',   '8765432109', '56 Jubilee Hills',     'Hyderabad','Telangana',   'India'),
('EMP005', 'Suresh Pillai',    'suresh.pillai@email.com',   '7654321098', '89 Residency Road',    'Bengaluru','Karnataka',   'India'),
('EMP006', 'Meera Krishnan',   'meera.krishnan@email.com',  '6543210987', '34 Park Street',       'Kolkata',  'West Bengal', 'India'),
('EMP007', 'Arjun Patel',      'arjun.patel@email.com',     '9871234560', '22 Drive-in Road',     'Ahmedabad','Gujarat',     'India'),
('EMP008', 'Divya Menon',      'divya.menon@email.com',     '9762345601', '11 Rajiv Chowk',       'Delhi',    'Delhi',       'India'),
('EMP009', 'Vikram Singh',     'vikram.singh@email.com',    '9653456712', '5 Mall Road',          'Shimla',   'HP',          'India'),
('EMP010', 'Lakshmi Iyer',     'lakshmi.iyer@email.com',    '9544567823', '67 Banjara Hills',     'Hyderabad','Telangana',   'India');

-- Update dashboard stats after seed
UPDATE dashboard_stats SET stat_value = 10 WHERE stat_key = 'total_records';
UPDATE dashboard_stats SET stat_value = 10 WHERE stat_key = 'total_unique';
