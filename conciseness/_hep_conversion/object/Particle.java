@Entity
public class Particle {
    @Id private Long particleId;
    private Integer pid;
    private Integer status;
    private Double mass;
    @Embedded private Momentum momentum;
    @ElementCollection private List<Integer> parentIds;
    @ElementCollection private List<Integer> childIds;
}
