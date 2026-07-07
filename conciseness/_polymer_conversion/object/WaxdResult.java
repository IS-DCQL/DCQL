@Entity
@Table(name = "waxd_results")
public class WaxdResult {
    @Id private String waxdId;
    private String processId;
    private Integer sampleNo;
    private Double paContent;
    private Double waxdPeak;
    private Double crystallinity;
    private Double crystalSize;
    private Double orientation;
}
