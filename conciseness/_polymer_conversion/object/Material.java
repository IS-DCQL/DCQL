@Entity
@Table(name = "materials")
public class Material {
    @Id private String materialId;
    private String name;
    private String smiles;
    private String repeatUnitSmiles;
    private String pid;
    private String category;            // Fully-Aromatic / Semi-Aromatic / Aliphatic
    private Double averageMw;
    private Double tensileModulus;
    private Double tensileStrength;
    private Double thermalDecomposition;
    private Double glassTemperature;
    private Double meltingTemperature;
    private Double heatDeflectionTemperature;
}
