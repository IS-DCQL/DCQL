package com.example.oqltest.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "diagnoses")
public class Diagnosis {
    @Id
    @Column(name = "diagnosis_id")
    private String diagnosisId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "case_id")
    private CaseEntity caseEntity;

    @Column(name = "primary_diagnosis")
    private String primaryDiagnosis;

    @Column(name = "vital_status")
    private String vitalStatus;

    @Column(name = "age_at_diagnosis")
    private Integer ageAtDiagnosis;

    private String morphology;

    @Column(name = "classification_of_tumor")
    private String classificationOfTumor;

    @Column(name = "tumor_grade")
    private String tumorGrade;

    @Column(name = "tissue_or_organ_of_origin")
    private String tissueOrOrganOfOrigin;

    public String getPrimaryDiagnosis() {
        return primaryDiagnosis;
    }

    public String getVitalStatus() {
        return vitalStatus;
    }
}
