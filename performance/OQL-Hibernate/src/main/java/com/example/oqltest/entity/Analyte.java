package com.example.oqltest.entity;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "analytes")
public class Analyte {
    @Id
    @Column(name = "analyte_id")
    private String analyteId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "portion_id")
    private Portion portion;

    @Column(name = "analyte_type")
    private String analyteType;

    private Double concentration;

    @OneToMany(mappedBy = "analyte", fetch = FetchType.LAZY)
    private List<Aliquot> aliquots;

    public String getAnalyteType() {
        return analyteType;
    }

    public List<Aliquot> getAliquots() {
        return aliquots;
    }
}
