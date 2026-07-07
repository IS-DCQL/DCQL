package com.example.oqltest.entity;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "samples")
public class Sample {
    @Id
    @Column(name = "sample_id")
    private String sampleId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "case_id")
    private CaseEntity caseEntity;

    @Column(name = "sample_type")
    private String sampleType;

    @Column(name = "tissue_type")
    private String tissueType;

    @Column(name = "specimen_type")
    private String specimenType;

    @Column(name = "tumor_descriptor")
    private String tumorDescriptor;

    @Column(name = "preservation_method")
    private String preservationMethod;

    @OneToMany(mappedBy = "sample", fetch = FetchType.LAZY)
    private List<Portion> portions;

    public String getSampleType() {
        return sampleType;
    }

    public String getPreservationMethod() {
        return preservationMethod;
    }

    public List<Portion> getPortions() {
        return portions;
    }
}
