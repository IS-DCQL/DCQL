@Entity
@Table(name = "processing_cases")
public class ProcessingCase {
    @Id private String processId;
    private String materialName;
    private String materialId;
    private Integer sampleNo;
    private String formulation;
    private Double speed;
    private Double pressure;
    private Double pressureTime;
    private Double coolingTemperature;
    private Double coolingTime;
    private Double injectionRate;
    private Double processingTemperature;
}
