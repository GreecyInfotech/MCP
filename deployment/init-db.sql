-- Enterprise AI Platform — Cloud SQL schema
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE,
    subject VARCHAR(500),
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sprint_metrics (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(20),
    sprint_name VARCHAR(100),
    story_points INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active'
);

INSERT INTO incidents (title, severity, status) VALUES
    ('API latency spike', 'high', 'resolved'),
    ('DB pool exhausted', 'critical', 'open')
ON CONFLICT DO NOTHING;

INSERT INTO sprint_metrics (project_key, sprint_name, story_points, status) VALUES
    ('PROJ', 'Sprint 24', 34, 'done'),
    ('PROJ', 'Sprint 23', 28, 'done')
ON CONFLICT DO NOTHING;
