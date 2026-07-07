// 3_benchmark.java — top-level reference copy of the benchmark runner.
//
// The compilable source that Maven builds lives at:
//   src/main/java/com/example/oqltest/runner/QueryBenchmarkRunner.java
// This file is an identical copy placed at the project root for convenient
// review; it is NOT on the Maven source path, so there is no double-compile.
// Run the benchmark with:  mvn -q spring-boot:run
package com.example.oqltest.runner;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Query;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Consolidated OQL-over-Hibernate benchmark runner.
 *
 * <p>Replaces the previous one-file-per-query scripts (1T2 / 1T3 / 1T3std /
 * 2T2 / 2T3). It times the FOUR T2/T3 queries of the two datasets:
 *
 * <ul>
 *   <li>biomedical T2 / T3 — JPQL over the entity classes (CaseEntity, ...)</li>
 *   <li>organic-polymer T2 / T3 — native SQL over the 5 {@code public} tables</li>
 * </ul>
 *
 * <p>The query TEXT is NOT embedded here. It is loaded at runtime from the
 * shared conciseness folder so the performance run executes the exact same
 * statements measured for conciseness:
 *
 * <pre>
 *   ../../conciseness/OQL/biomedical/T2.jpql       (JPQL)
 *   ../../conciseness/OQL/biomedical/T3.jpql       (JPQL)
 *   ../../conciseness/OQL/organic-polymer/T2.sql   (native SQL)
 *   ../../conciseness/OQL/organic-polymer/T3.sql   (native SQL)
 * </pre>
 *
 * <p>Timing methodology is preserved from the original scripts: each query is
 * warmed up, then run for a number of measured rounds; per-round wall time is
 * taken with {@link System#nanoTime()} around {@code getResultList()} and the
 * Hibernate {@link Statistics} execution time/count are recorded. The fastest
 * and slowest 20% of measured rounds are trimmed and the mean + sample standard
 * deviation are reported.
 */
@Component
public class QueryBenchmarkRunner implements CommandLineRunner {

    @PersistenceContext
    private EntityManager entityManager;

    private final EntityManagerFactory entityManagerFactory;

    public QueryBenchmarkRunner(EntityManagerFactory entityManagerFactory) {
        this.entityManagerFactory = entityManagerFactory;
    }

    private static final int WARMUP_ROUNDS = 3;

    /** Point queries (T2) tolerate many rounds; heavy screens (T3) fewer. */
    private static final int POINT_TEST_ROUNDS = 500;
    private static final int HEAVY_TEST_ROUNDS = 20;

    private static final int LIMIT = 50;

    /**
     * Directory holding the shared query statements, resolved relative to the
     * Maven project root (the working directory when running `mvn ...`).
     * Override with -Dqueries.dir=/abs/path if needed.
     */
    private static final String DEFAULT_QUERIES_DIR = "../../conciseness/OQL";

    /** Describes one query to benchmark. */
    private enum QueryType { JPQL, SQL }

    private static final class BenchmarkCase {
        final String label;
        final String relativePath;   // relative to the queries dir
        final QueryType type;
        final int testRounds;

        BenchmarkCase(String label, String relativePath, QueryType type, int testRounds) {
            this.label = label;
            this.relativePath = relativePath;
            this.type = type;
            this.testRounds = testRounds;
        }
    }

    private static final List<BenchmarkCase> CASES = List.of(
            new BenchmarkCase("biomedical T2 (JPQL)", "biomedical/T2.jpql", QueryType.JPQL, POINT_TEST_ROUNDS),
            new BenchmarkCase("biomedical T3 (JPQL)", "biomedical/T3.jpql", QueryType.JPQL, HEAVY_TEST_ROUNDS),
            new BenchmarkCase("organic-polymer T2 (native SQL)", "organic-polymer/T2.sql", QueryType.SQL, HEAVY_TEST_ROUNDS),
            new BenchmarkCase("organic-polymer T3 (native SQL)", "organic-polymer/T3.sql", QueryType.SQL, HEAVY_TEST_ROUNDS)
    );

    @Override
    @Transactional
    public void run(String... args) throws Exception {
        Path queriesDir = Path.of(System.getProperty("queries.dir", DEFAULT_QUERIES_DIR));

        SessionFactory sessionFactory = entityManagerFactory.unwrap(SessionFactory.class);
        Statistics statistics = sessionFactory.getStatistics();
        statistics.setStatisticsEnabled(true);

        System.out.println("==================================================");
        System.out.println("OQL / Hibernate query benchmark (T2 / T3, 4 queries)");
        System.out.println("Query-statement source directory: " + queriesDir.toAbsolutePath());
        System.out.println("Timing method: System.nanoTime() around getResultList() + Hibernate Statistics");
        System.out.println("==================================================\n");

        for (BenchmarkCase bc : CASES) {
            Path queryPath = queriesDir.resolve(bc.relativePath);
            String queryText = Files.readString(queryPath).trim();
            benchmark(statistics, bc, queryText);
        }
    }

    private void benchmark(Statistics statistics, BenchmarkCase bc, String queryText) {
        System.out.println("##################################################");
        System.out.println("# " + bc.label);
        System.out.println("# File: " + bc.relativePath);
        System.out.println("##################################################");
        System.out.println("---------- query statement ----------");
        System.out.println(queryText);
        System.out.println("------------------------------\n");

        System.out.println("========== warm-up phase (" + WARMUP_ROUNDS + " rounds) ==========");
        for (int i = 1; i <= WARMUP_ROUNDS; i++) {
            runOnce(statistics, bc, queryText, false, i, "warm-up");
        }

        System.out.println("\n========== measured phase (" + bc.testRounds + " rounds) ==========");

        List<Long> elapsedNsList = new ArrayList<>();
        long totalQueryCount = 0;
        long minNs = Long.MAX_VALUE;
        long maxNs = Long.MIN_VALUE;

        for (int i = 1; i <= bc.testRounds; i++) {
            QueryRunResult result = runOnce(statistics, bc, queryText, true, i, "measured");
            elapsedNsList.add(result.elapsedNs);
            totalQueryCount += result.queryExecutionCount;
            minNs = Math.min(minNs, result.elapsedNs);
            maxNs = Math.max(maxNs, result.elapsedNs);
        }

        elapsedNsList.sort(Long::compareTo);

        int removeCount = (int) (bc.testRounds * 0.2);
        int startIndex = removeCount;
        int endIndex = bc.testRounds - removeCount;

        long trimmedTotalNs = 0;
        List<Long> trimmed = new ArrayList<>();
        for (int i = startIndex; i < endIndex; i++) {
            long value = elapsedNsList.get(i);
            trimmedTotalNs += value;
            trimmed.add(value);
        }
        int trimmedCount = trimmed.size();

        double avgUs = trimmedTotalNs / 1000.0 / trimmedCount;
        double avgMs = trimmedTotalNs / 1_000_000.0 / trimmedCount;

        double squaredDiffSum = 0.0;
        for (Long value : trimmed) {
            double diffUs = value / 1000.0 - avgUs;
            squaredDiffSum += diffUs * diffUs;
        }
        double sampleStdDevUs = trimmedCount > 1
                ? Math.sqrt(squaredDiffSum / (trimmedCount - 1))
                : 0.0;

        System.out.println("\n---------- execution-time statistics ----------");
        System.out.println("Measured rounds: " + bc.testRounds);
        System.out.println("Query executions recorded by Hibernate: " + totalQueryCount);
        System.out.println("Fastest 20% dropped (rounds): " + removeCount);
        System.out.println("Slowest 20% dropped (rounds): " + removeCount);
        System.out.println("Rounds included in the mean: " + trimmedCount);
        System.out.printf("Mean query-execution time after trimming the fastest/slowest 20%%: %.3f μs / %.6f ms%n", avgUs, avgMs);
        System.out.printf("Sample standard deviation after trimming the fastest/slowest 20%%: %.3f μs / %.6f ms%n",
                sampleStdDevUs, sampleStdDevUs / 1000.0);
        System.out.printf("Fastest single query-execution time: %.3f μs%n", minNs / 1000.0);
        System.out.printf("Slowest single query-execution time: %.3f μs%n", maxNs / 1000.0);
        System.out.println("==================================================\n\n");
    }

    @SuppressWarnings("unchecked")
    private QueryRunResult runOnce(
            Statistics statistics,
            BenchmarkCase bc,
            String queryText,
            boolean printResult,
            int round,
            String phase
    ) {
        statistics.clear();

        Query query;
        if (bc.type == QueryType.JPQL) {
            query = entityManager.createQuery(queryText);
        } else {
            query = entityManager.createNativeQuery(queryText);
        }

        // Bind the named parameters used by each statement (only if present in
        // the loaded text). Polymer T2/T3 use SQL literals -> no binding.
        bindParameters(query, queryText, bc);

        if (queryText.contains(":projectIds")) {
            query.setMaxResults(LIMIT);
        }

        long startNs = System.nanoTime();
        List<Object[]> results = query.getResultList();
        long endNs = System.nanoTime();

        long elapsedNs = endNs - startNs;
        long queryExecutionCount = statistics.getQueryExecutionCount();

        System.out.printf(
                "%s round %d done, elapsed: %.3f μs / %.6f ms, result count: %d%n",
                phase, round, elapsedNs / 1000.0, elapsedNs / 1_000_000.0, results.size());

        if (printResult && round == 1) {
            System.out.println("\n---------- sample query results (up to 5 rows) ----------");
            int shown = 0;
            for (Object row : results) {
                if (shown++ >= 5) break;
                if (row instanceof Object[]) {
                    System.out.println(Arrays.toString((Object[]) row));
                } else {
                    System.out.println(row);
                }
            }
            System.out.println("--------------------------------------------\n");
        }

        return new QueryRunResult(elapsedNs, queryExecutionCount);
    }

    /**
     * Bind only the named parameters that actually appear in the query text,
     * with the experiment values used by the original benchmark scripts.
     */
    private void bindParameters(Query query, String queryText, BenchmarkCase bc) {
        // biomedical T2 — point query by case_id
        if (queryText.contains(":caseId")) {
            query.setParameter("caseId", "00016c8f-a0be-4319-9c42-4f3bcd90ac92");
        }
        // biomedical T3 — multi-join filtered screen
        if (queryText.contains(":projectIds")) {
            query.setParameter("projectIds", Arrays.asList("TCGA-KIRC", "TARGET-WT"));
            query.setParameter("deadStatus", "Dead");
            query.setParameter("diagnosisKeyword", "%renal cell carcinoma%");
            query.setParameter("sampleType", "Primary Tumor");
            query.setParameter("preservationMethods",
                    Arrays.asList("Snap Frozen", "Snap-Frozen", "OCT"));
            query.setParameter("analyteType", "RNA");
            query.setParameter("minConcentration", 0.1);
        }
        // organic-polymer native SQL uses literals; bind here only if a future
        // parameterised variant is supplied.
        if (queryText.contains(":polymerName")) {
            query.setParameter("polymerName", "1252 (PA66-48%, PA6T-52%)");
        }
        if (queryText.contains(":category")) {
            query.setParameter("category", "Semi-Aromatic");
            query.setParameter("tmThreshold", 280);
            query.setParameter("strengthThreshold", 150);
            query.setParameter("speedThreshold", 50);
        }
    }

    private static final class QueryRunResult {
        final long elapsedNs;
        final long queryExecutionCount;

        QueryRunResult(long elapsedNs, long queryExecutionCount) {
            this.elapsedNs = elapsedNs;
            this.queryExecutionCount = queryExecutionCount;
        }
    }
}
