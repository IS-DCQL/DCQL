@Entity
public class Portion {
    @Id private String portionId;
    private Integer portionNumber;
    private Double weight;
    private Boolean isFfpe;
    @ElementCollection private List<Slide> slides;   // slides embedded as value objects
    @OneToMany private List<Analyte> analytes;       // 1 : N
}
