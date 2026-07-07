@Entity
public class Project {
    @Id private String projectId;
    private String projectName;
    @OneToMany(mappedBy = "project") private List<Case> cases;
}
