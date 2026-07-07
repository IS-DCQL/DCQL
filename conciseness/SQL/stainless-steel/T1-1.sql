CREATE TABLE pesr_hns_protocol (
    protocol_id VARCHAR PRIMARY KEY,
    grade       VARCHAR
);
CREATE TABLE composition (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    element VARCHAR, content NUMERIC, unit VARCHAR DEFAULT '%'
);
CREATE TABLE process_parameter (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    name VARCHAR, value VARCHAR
);
CREATE TABLE microstructure (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    description VARCHAR
);
CREATE TABLE performance_indicator (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    name VARCHAR, value NUMERIC, unit VARCHAR
);
