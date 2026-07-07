package com.example.oqltest.entity;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "portions")
public class Portion {
    @Id
    @Column(name = "portion_id")
    private String portionId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sample_id")
    private Sample sample;

    @Column(name = "portion_number")
    private String portionNumber;

    @Column(name = "is_ffpe")
    private String isFfpe;

    @OneToMany(mappedBy = "portion", fetch = FetchType.LAZY)
    private List<Analyte> analytes;

    public List<Analyte> getAnalytes() {
        return analytes;
    }
}
