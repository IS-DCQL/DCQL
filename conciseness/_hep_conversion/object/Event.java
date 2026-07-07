@Entity
public class Event {
    @Id private Integer eventNumber;
    private String momentumUnit;
    private String lengthUnit;
    @OneToMany private List<Particle> particles;
}
