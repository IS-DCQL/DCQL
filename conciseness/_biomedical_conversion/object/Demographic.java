@Entity
public class Demographic {
    @Id private String demographicId;
    private String ethnicity;
    private String gender;
    private String race;
    private String vitalStatus;
    private String sexAtBirth;
    private Integer daysToBirth;
}
