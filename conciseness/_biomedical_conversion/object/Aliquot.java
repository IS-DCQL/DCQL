@Entity
public class Aliquot {
    @Id private String aliquotId;
    private String analyteType;
    private Double aliquotQuantity;
    private Double aliquotVolume;
    private Double concentration;
    private String sourceCenter;
}
