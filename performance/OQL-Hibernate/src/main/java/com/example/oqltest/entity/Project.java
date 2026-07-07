package com.example.oqltest.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "projects")
public class Project {
    @Id
    @Column(name = "project_id")
    private String projectId;

    public String getProjectId() {
        return projectId;
    }
}
