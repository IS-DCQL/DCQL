@Entity
public class Analyte {
    @Id private String analyteId;
    private String analyteType;
    private Double concentration;
    private Double rnaIntegrityNumber;
    private Double a260A280Ratio;
    @OneToMany private List<Aliquot> aliquots;   // 1 : N
}
