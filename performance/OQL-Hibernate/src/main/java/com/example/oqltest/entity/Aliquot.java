package com.example.oqltest.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "aliquots")
public class Aliquot {
    @Id
    @Column(name = "aliquot_id")
    private String aliquotId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analyte_id")
    private Analyte analyte;

    @Column(name = "submitter_id")
    private String submitterId;

    private String state;
    private Double concentration;

    @Column(name = "aliquot_quantity")
    private Double aliquotQuantity;

    @Column(name = "aliquot_volume")
    private Double aliquotVolume;

    public String getAliquotId() {
        return aliquotId;
    }

    public Double getConcentration() {
        return concentration;
    }
}
