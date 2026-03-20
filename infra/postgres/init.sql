-- Initialize BaiCao database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE verification_status AS ENUM ('verified', 'pending', 'rejected');
CREATE TYPE source_type AS ENUM ('ancient', 'modern', 'patent', 'database');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE baicao TO baicao;
