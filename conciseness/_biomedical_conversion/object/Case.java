@Entity
public class Case {
    @Id private String caseId;
    @ManyToOne private Project project;        // Case N : 1 Project
    private String primarySite;
    private String diseaseType;
    private String submitterId;
    private String state;
    @OneToOne private Demographic demographic;  // Case 1 : 1 Demographic
    @OneToMany private List<Diagnosis> diagnoses;   // 1 : N
    @OneToMany private List<Sample> samples;        // 1 : N
}
