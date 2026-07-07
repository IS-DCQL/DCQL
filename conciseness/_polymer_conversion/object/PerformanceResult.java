@Entity
@Table(name = "performance_results")
public class PerformanceResult {
    @Id private String performanceId;
    private String processId;
    private Integer sampleNo;
    private Double tensileStrength;
    private Double tensileModulus;
    private Double elongation;
    private Double impactStrength;
}
