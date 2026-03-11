-- Создание баз данных для каждого микросервиса
CREATE DATABASE user_service;
CREATE DATABASE device_registry;
CREATE DATABASE heating_service;
CREATE DATABASE lighting_service;
CREATE DATABASE access_service;
CREATE DATABASE scenarios_service;

-- Подключаемся к user_service и создаем таблицы
\c user_service;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    avatar_url TEXT
);

CREATE TABLE homes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    owner_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE home_users (
    user_id UUID REFERENCES users(id),
    home_id UUID REFERENCES homes(id),
    role_id UUID,
    status VARCHAR(50) DEFAULT 'active',
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, home_id)
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    home_id UUID NOT NULL REFERENCES homes(id),
    permissions JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, home_id)
);

CREATE TABLE invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    home_id UUID NOT NULL REFERENCES homes(id),
    invited_by UUID NOT NULL REFERENCES users(id),
    role_id UUID NOT NULL REFERENCES roles(id),
    status VARCHAR(50) DEFAULT 'pending',
    token VARCHAR(255) UNIQUE,
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id),
    plan_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    auto_renew BOOLEAN DEFAULT TRUE
);

-- Подключаемся к device_registry
\c device_registry;

CREATE TABLE device_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    protocol VARCHAR(50) NOT NULL,
    capabilities JSONB NOT NULL,
    supported_commands JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(vendor, model)
);

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    model_id UUID NOT NULL REFERENCES device_models(id),
    name VARCHAR(255),
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    auth_token VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'inactive',
    firmware_version VARCHAR(50),
    last_seen_at TIMESTAMP,
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Подключаемся к heating_service
\c heating_service;

CREATE TABLE thermostats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID UNIQUE NOT NULL,
    current_temp FLOAT,
    target_temp FLOAT,
    mode VARCHAR(20) DEFAULT 'off',
    humidity INT,
    battery INT,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE TABLE temperature_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    temperature FLOAT NOT NULL,
    humidity INT,
    battery INT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE heating_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    name VARCHAR(255),
    days_of_week JSONB NOT NULL,
    time TIME NOT NULL,
    target_temp FLOAT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Подключаемся к lighting_service
\c lighting_service;

CREATE TABLE lights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID UNIQUE NOT NULL,
    power BOOLEAN DEFAULT FALSE,
    brightness INT DEFAULT 100,
    color_hex VARCHAR(7),
    color_temperature INT,
    online BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE TABLE light_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    device_ids JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE lighting_scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    actions JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Подключаемся к access_service
\c access_service;

CREATE TABLE locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID UNIQUE NOT NULL,
    state VARCHAR(20) DEFAULT 'locked',
    battery INT,
    last_action TIMESTAMP,
    last_action_by UUID
);

CREATE TABLE gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID UNIQUE NOT NULL,
    state VARCHAR(20) DEFAULT 'closed',
    last_action TIMESTAMP,
    last_action_by UUID
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_id UUID NOT NULL,
    actions JSONB NOT NULL,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL
);

CREATE TABLE temporary_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    phone VARCHAR(20),
    device_id UUID NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP NOT NULL,
    uses INT DEFAULT 0,
    max_uses INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    device_id UUID,
    action VARCHAR(100) NOT NULL,
    result VARCHAR(20) NOT NULL,
    details JSONB,
    ip_address INET,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Подключаемся к scenarios_service
\c scenarios_service;

CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger JSONB NOT NULL,
    conditions JSONB,
    actions JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE scenario_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id),
    triggered_at TIMESTAMP NOT NULL,
    trigger_data JSONB,
    actions JSONB,
    status VARCHAR(20) DEFAULT 'completed',
    error TEXT,
    completed_at TIMESTAMP
);