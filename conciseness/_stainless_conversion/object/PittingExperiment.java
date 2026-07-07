@Entity
public class PittingExperiment {
    @Id private String expId;
    private String grade;
    private String materialName;
    private String microstructure;
    private String methodName;
    private Double yieldStrengthMpa;
    @ElementCollection private Map<String, String> elementContent;
    private Double naclWt;
    private Double temperatureC;
    private Double scanRateMvMin;
    @Embedded private CorrosionResult result;
}
