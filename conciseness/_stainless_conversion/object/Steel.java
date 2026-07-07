@Entity
public class Steel {
    @Id private String steelId;
    private String grade;
    private String specimenShape;
    private String heatTreatment;
    @ElementCollection private List<Composition> composition;
    @Embedded private MechanicalProperty mechanicalProperty;
}
