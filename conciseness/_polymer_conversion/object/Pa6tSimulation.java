@Entity
@Table(name = "pa6t_simulations")
public class Pa6tSimulation {
    @Id private String simulationId;
    private Double pa6tContent;
    private Double temperature;
    private Double density;
    private Double energy;
    private Double transitionTemperature;
}
