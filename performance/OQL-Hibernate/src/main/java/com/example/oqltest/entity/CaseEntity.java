package com.example.oqltest.entity;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "cases")
public class CaseEntity {
    @Id
    @Column(name = "case_id")
    private String caseId;

    @Column(name = "primary_site")
    private String primarySite;

    @Column(name = "disease_type")
    private String diseaseType;

    @Column(name = "submitter_id")
    private String submitterId;

    private String state;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "project_id")
    private Project project;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "demographic_id")
    private Demographic demographic;

    @OneToMany(mappedBy = "caseEntity", fetch = FetchType.LAZY)
    private List<Diagnosis> diagnoses;

    @OneToMany(mappedBy = "caseEntity", fetch = FetchType.LAZY)
    private List<Sample> samples;

    public String getCaseId() {
        return caseId;
    }

    public Project getProject() {
        return project;
    }

    public Demographic getDemographic() {
        return demographic;
    }

    public List<Diagnosis> getDiagnoses() {
        return diagnoses;
    }

    public List<Sample> getSamples() {
        return samples;
    }
}
