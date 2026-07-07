@Entity
public class Diagnosis {
    @Id private String diagnosisId;
    private String primaryDiagnosis;
    private String morphology;
    private String tissueOrOrganOfOrigin;
    private String siteOfResectionOrBiopsy;
    private Integer ageAtDiagnosis;
    private String classificationOfTumor;
    private String tumorGrade;
    private String lastKnownDiseaseStatus;
}
