@Entity
public class Sample {
    @Id private String sampleId;
    private String sampleType;
    private String tissueType;
    private String specimenType;
    private String tumorDescriptor;
    private String preservationMethod;
    @OneToMany private List<Portion> portions;   // 1 : N
}
