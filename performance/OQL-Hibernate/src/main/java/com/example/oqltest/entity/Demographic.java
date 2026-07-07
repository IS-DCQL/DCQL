package com.example.oqltest.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "demographics")
public class Demographic {
    @Id
    @Column(name = "demographic_id")
    private String demographicId;

    @Column(name = "case_id")
    private String caseId;

    private String gender;
    private String race;
    private String ethnicity;

    @Column(name = "vital_status")
    private String vitalStatus;

    @Column(name = "sex_at_birth")
    private String sexAtBirth;

    @Column(name = "age_at_index")
    private Integer ageAtIndex;

    public String getDemographicId() {
        return demographicId;
    }

    public String getVitalStatus() {
        return vitalStatus;
    }
}
