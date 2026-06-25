const DATA = {
  summary: "data/site_summary.json",
  backends: "data/backend_coverage.json",
  alignment: "data/spectre_alignment_table.json",
  tasks: "data/task_gallery.json",
  taskDetails: "data/task_details.json",
  categories: "data/category_coverage.json",
  modelRoster: "data/model_eval_roster.json",
  precision: "data/precision_overview.json",
};

const LANGUAGE_KEY = "vabench-dashboard-language";

const NEWS_ITEMS = [
  {
    date: "2026-06-22",
    type: "Docs",
    title: {
      en: "Benchmark rows and precision cases are now clickable",
      zh: "Benchmark 行和精度案例现在可以点进详情页",
    },
    body: {
      en: "Each released row can open a task detail page, and task-metric precision rows can open a case page explaining the concrete RMS caveats.",
      zh: "每个 released row 都可以进入单题详情；task-metric 精度行也可以进入案例页，查看具体 RMS 说明。",
    },
    href: "benchmark.html",
  },
  {
    date: "2026-06-22",
    type: "Accuracy",
    title: {
      en: "Precision overview separates equivalence from bit-exact equality",
      zh: "精度总览区分等价通过与 bit-exact 完全相同",
    },
    body: {
      en: "Accuracy now reports full-300 common-row precision evidence, task-metric rows, and pointwise-difference caveats.",
      zh: "Accuracy 页面现在报告 full-300 common-row 精度证据、task-metric 行和逐点差异说明。",
    },
    href: "accuracy.html",
  },
  {
    date: "2026-06-22",
    type: "Docs",
    title: {
      en: "GitHub Pages deployment workflow",
      zh: "GitHub Pages 部署 workflow",
    },
    body: {
      en: "The docs/ site can now be published by GitHub Pages using the checked-in Actions workflow.",
      zh: "docs/ 站点现在可以通过仓库中的 Actions workflow 发布到 GitHub Pages。",
    },
    href: "index.html",
  },
  {
    date: "2026-06-22",
    type: "Release",
    title: {
      en: "Model evaluation guide and unified runner",
      zh: "模型评测指南与统一 runner",
    },
    body: {
      en: "Added a public Run Models page for OpenAI-compatible and Anthropic-compatible model evaluation, including DeepSeek V4 Flash smoke commands.",
      zh: "新增 Run Models 页面，说明 OpenAI-compatible 与 Anthropic-compatible 模型接入，并给出 DeepSeek V4 Flash smoke 命令。",
    },
    href: "run-model-eval.html",
  },
  {
    date: "2026-06-22",
    type: "Benchmark",
    title: {
      en: "vaBench is organized as one 300-row denominator",
      zh: "vaBench 统一为 300 行管理分母",
    },
    body: {
      en: "The 271 inherited rows and 29 promoted rows are now managed as one vaBench 300 surface, with provenance retained only as an audit label.",
      zh: "271 个继承行和 29 个新增行统一管理为 vaBench 300；来源只作为审计标签保留。",
    },
    href: "benchmark.html",
  },
  {
    date: "2026-06-22",
    type: "Protocol",
    title: {
      en: "Golden alignment table clarifies tolerance-gated equivalence",
      zh: "Golden 对齐表明确容差等价口径",
    },
    body: {
      en: "The protocol page separates bit-exact claims from waveform/task-metric parity and keeps Spectre as the final judge.",
      zh: "Protocol 页面区分 bit-exact 与 waveform/task-metric parity，并保持 Spectre 为最终判定。",
    },
    href: "protocol.html",
  },
  {
    date: "2026-06-22",
    type: "Docs",
    title: {
      en: "Website navigation split into benchmark-facing pages",
      zh: "网站导航拆为面向 benchmark 的页面",
    },
    body: {
      en: "Home, Leaderboard, Benchmark, Run Models, Protocol, News, and Contributors now map to separate reader intents.",
      zh: "Home、Leaderboard、Benchmark、Run Models、Protocol、News、Contributors 分别对应不同读者意图。",
    },
    href: "index.html",
  },
];

const VERIFIED_LEADERBOARD_ROWS = [];

const SMOKE_ROWS = [
  {
    model: "deepseek-v4-flash",
    provider: "DeepSeek",
    status: "integration_smoke_passed",
    evas: "generated + scored 1 row; candidate failed behavior correctness",
    spectre: "not run",
  },
];

const I18N = {
  en: {
    brandSubtitle: "Behavioral Verilog-A Benchmark",
    navHome: "Home",
    navLeaderboard: "Leaderboard",
    navBenchmark: "Benchmark",
    navRunModels: "Run Models",
    navProtocol: "Protocol",
    navAccuracy: "Accuracy",
    navNews: "News",
    navContributors: "Contributors",
    navBlog: "Blog",
    navRun: "Run",
    navData: "Data",
    navGithub: "GitHub",
    languageToggle: "中文",
    languageToggleAria: "Switch site language to Chinese",
    footerGenerated: "Generated from vaBench release reports.",
    homeEyebrow: "Behavioral Verilog-A evaluation",
    homeTitle: "vaBench 300",
    homeText:
      "Measuring frontier models on analog and mixed-signal behavioral Verilog-A tasks with EVAS fast gates and Spectre final judging.",
    homePrimaryAction: "Run vaBench",
    homeSecondaryAction: "Browse data",
    featureBenchmarkEyebrow: "Benchmark",
    featureBenchmarkTitle: "300 certified forms",
    featureBenchmarkBody: "Browse tasks by category, level, form, score surface, and provenance.",
    featureLeaderboardEyebrow: "Leaderboard",
    featureLeaderboardTitle: "Spectre final judge",
    featureLeaderboardBody: "Separate verified Spectre-scored runs from integration smoke tests.",
    featureProtocolEyebrow: "Protocol",
    featureProtocolTitle: "EVAS/Spectre gates",
    featureProtocolBody: "Track four-backend certification, golden alignment, and tolerance rules.",
    featureAccuracyEyebrow: "Accuracy",
    featureAccuracyTitle: "Precision evidence",
    featureAccuracyBody: "See whether EVAS and Spectre are bit-identical, equivalent, or numerically different.",
    homeLeaderboardEyebrow: "Leaderboard",
    homeLeaderboardTitle: "Leaderboard",
    homeLeaderboardBody:
      "Verified rows require Spectre final judging. EVAS-only runs and API smoke tests stay visible as integration evidence, not ranked benchmark scores.",
    homeLeaderboardFootnote:
      "Core leaderboard denominator: 265 core score forms. The 35 certified support forms are reported separately.",
    leaderboardVersionCurrent: "v300",
    leaderboardVersionCore: "Core score",
    leaderboardVersionSupport: "Support forms",
    leaderboardMetricScore: "Pass@1",
    leaderboardMetricJudge: "Spectre judge",
    homeNewsEyebrow: "News",
    homeNewsTitle: "Latest updates",
    viewAllNews: "View all news",
    whyEyebrow: "Why vaBench",
    whyTitle: "Built for behavioral circuit modeling",
    whyBody:
      "vaBench is a public benchmark for analog and mixed-signal behavioral Verilog-A generation. It keeps task content, reference artifacts, deterministic checkers, EVAS fast gates, and Spectre final judging visible as separate pieces of evidence.",
    taskExamplesEyebrow: "Task examples",
    taskExamplesTitle: "A few rows from vaBench 300",
    taskExamplesBody:
      "Each example links to the exact prompt, reference artifacts, checker contract, certification status, and EVAS/Spectre precision evidence.",
    viewAllTasks: "All 300 tasks",
    homeReadEyebrow: "Read the protocol",
    homeReadTitle: "How vaBench is scored and certified",
    homeReadBody:
      "The protocol separates public benchmark tasks, core score forms, support forms, EVAS fast gates, Spectre final judging, and tolerance-gated parity evidence.",
    homeReadProtocol: "Open protocol",
    homeReadAccuracy: "View accuracy",
    leaderboardEyebrow: "Leaderboard",
    leaderboardPageTitle: "vaBench model leaderboard",
    leaderboardPageText:
      "Verified rows require Spectre final judging. EVAS-only runs and API smoke tests are shown as integration evidence, not ranked benchmark scores.",
    verifiedRunsEyebrow: "Verified runs",
    verifiedRunsTitle: "Spectre-scored submissions",
    verifiedRunsDescription: "This table stays empty until a model has run the scored roster with Spectre final judge enabled.",
    integrationEyebrow: "Integration status",
    integrationTitle: "Smoke-tested model access",
    submitRunTitle: "Submit or reproduce a run",
    submitRunText: "Use the unified runner first. Publish the top-level summary when a result is ready to rank.",
    benchmarkEyebrow: "Benchmark",
    benchmarkPageTitle: "vaBench 300 task set",
    benchmarkPageText:
      "Browse the benchmark by function family, task form, level, difficulty, and score surface. The public management denominator is 300 rows; the current core-score roster is 265 forms plus 35 certified support forms reported separately.",
    coverageEyebrow: "Coverage",
    coverageTitle: "Function categories",
    coverageDescription: "Entry and row coverage across analog and mixed-signal behavioral function families.",
    taskGalleryEyebrow: "Task gallery",
    taskGalleryTitle: "Released rows",
    taskGalleryDescription: "Search and filter the 300 rows. Click a task name to inspect its public assets, backend status, and precision evidence.",
    idGuideTitle: "Identifier guide",
    idGuideVbr1: "vaBench release v1 inherited entry namespace; not a count, rank, or score.",
    idGuideVbr11: "historical spelling for vaBench v1.1 promoted entries added to the 300-row surface.",
    idGuideLevel: "benchmark level: reusable function rows versus composed flow rows.",
    idGuideForm: "form suffix inside one entry; these are rows in the 300-row denominator.",
    benchmarkDetailEyebrow: "Benchmark detail",
    benchmarkDetailTitle: "Benchmark row detail",
    benchmarkDetailText:
      "Inspect one released row: public task identity, benchmark contents, certification status, and EVAS/Spectre precision evidence.",
    taskDetailBack: "Back to benchmark",
    taskDetailMissing: "Task row not found",
    taskDetailMissingBody: "The URL does not match a released vaBench row. Return to the benchmark table and open a row from there.",
    taskDetailIdentityTitle: "Task identity",
    taskDetailAssetsTitle: "Public assets",
    taskDetailEvaluationTitle: "Certification and parity",
    taskDetailPrecisionTitle: "Precision evidence",
    taskDetailContentsEyebrow: "Benchmark contents",
    taskDetailContentsTitle: "Core benchmark files",
    taskDetailContentsDescription:
      "Start with the four files people usually need to inspect: task prompt, reference answer, reference testbench, and evaluation checks. Metadata and manifests are kept below as advanced raw files.",
    taskDetailNoContents: "No inline benchmark contents are available for this row.",
    taskDetailCorePromptTitle: "Task prompt",
    taskDetailCorePromptBody: "The exact public prompt given to model submissions.",
    taskDetailCoreAnswerTitle: "Reference answer",
    taskDetailCoreAnswerBody: "Gold Verilog-A source files used as the reference implementation. Multi-module e2e rows may have more than one source file.",
    taskDetailCoreTestbenchTitle: "Reference testbench",
    taskDetailCoreTestbenchBody: "Spectre testbench files used to exercise the reference implementation.",
    taskDetailCoreEvaluationTitle: "Evaluation checks",
    taskDetailCoreEvaluationBody: "Machine-readable checker contract for syntax, compile, simulation correctness, and parity.",
    taskDetailCoreSuppliedTitle: "Supplied/support artifacts",
    taskDetailCoreSuppliedBody: "Original inputs or support files that are part of the task context, such as buggy sources in bugfix rows.",
    taskDetailAdvancedTitle: "Advanced raw files",
    taskDetailAdvancedDescription: "Machine metadata and complete raw export files for audit and runner integration.",
    taskDetailAccuracyCasesTitle: "Related accuracy cases",
    taskDetailNoAccuracyCase: "No task-metric accuracy case is recorded for this row.",
    openPrompt: "Open prompt",
    openChecks: "Open checks",
    openMeta: "Open meta",
    openReleaseManifest: "Open release task",
    openEvidence: "Open evidence",
    openSource: "Open source",
    fileMissing: "File not found in the website export.",
    fileTruncated: "Truncated in the website export.",
    fileBytes: "{count} bytes",
    contentKindPrompt: "Prompt",
    contentKindChecks: "Checker",
    contentKindMeta: "Metadata",
    contentKindReleaseTask: "Release task",
    contentKindGold: "Gold/reference artifact",
    contentKindReferenceAnswer: "Reference answer",
    contentKindReferenceTestbench: "Reference testbench",
    contentKindSuppliedArtifact: "Supplied/support artifact",
    protocolEyebrow: "Protocol",
    protocolPageTitle: "Evaluation and certification gates",
    protocolPageText:
      "Spectre is the final judge. EVAS is a fast evaluator that must remain aligned with Spectre on the supported voltage-domain/event-driven subset.",
    backendCertificationEyebrow: "Backend certification",
    backendCertificationTitle: "Four execution surfaces",
    backendCertificationDescription: "These rows certify the benchmark and evaluator surfaces, not model leaderboard rankings.",
    claimBoundaryEyebrow: "Claim boundary",
    claimBoundaryTitle: "What can be claimed",
    parityGatesEyebrow: "Parity gates",
    alignmentEyebrow: "Spectre alignment",
    alignmentTitle: "Golden reference equivalence table",
    alignmentDescription:
      "Each row states what was compared, the measured EVAS/Spectre difference, and the tolerance gate. Bit-exact equality is not asserted.",
    accuracyEyebrow: "Accuracy",
    accuracyPageTitle: "EVAS and Spectre precision",
    accuracyPageText:
      "The benchmark does not claim bit-exact equality. It reports whether each surface is behavior-equivalent to the Spectre reference under explicit gates.",
    accuracyCaseEyebrow: "Accuracy case",
    accuracyCaseTitle: "Precision case detail",
    accuracyCaseText:
      "Inspect one task-metric precision case and the concrete reason why raw pointwise RMS is diagnostic rather than the acceptance score.",
    accuracyCaseBack: "Back to accuracy",
    accuracyCaseMissing: "Accuracy case not found",
    accuracyCaseMissingBody: "The URL does not match a recorded task-metric precision row. Open a case from the Accuracy table.",
    accuracyCaseMetricsTitle: "Case metrics",
    accuracyCaseTaskTitle: "Related benchmark row",
    accuracyCaseWhyTitle: "Why raw RMS can be large here",
    accuracyCaseWhyText:
      "These notes are case-specific reading aids. They document why the current gate accepts the row and where EVAS or the checker can still improve.",
    accuracyCaseTaskLink: "Open benchmark row",
    accuracyIdenticalEyebrow: "Equivalence answer",
    accuracyIdenticalTitle: "Are the outputs exactly identical?",
    accuracyTermsEyebrow: "Reading tolerance",
    accuracyTermsTitle: "What the gate means",
    precisionStrictEyebrow: "Four-way reference",
    precisionStrictTitle: "Precision vs Spectre strict",
    precisionStrictDescription:
      "EVAS Python, EVAS Rust, and Spectre AX are compared against the same Spectre strict reference on the current full-300 common-row set.",
    spectreAnchorEyebrow: "Tolerance anchor",
    spectreAnchorTitle: "Spectre AX vs classic",
    spectreAnchorDescription:
      "Official Spectre modes are not bit-identical either. This self-consistency report is the reference anchor for deciding what waveform drift is acceptable before calling EVAS mismatched.",
    newsEyebrow: "News",
    newsPageTitle: "Updates and release notes",
    newsPageText: "Track benchmark, evaluator, runner, and documentation changes in one human-readable timeline.",
    contributorsEyebrow: "Contributors",
    contributorsPageTitle: "People and attribution",
    contributorsPageText: "A lightweight place for benchmark maintainers, task authors, evaluator contributors, and citation instructions.",
    maintainersEyebrow: "Maintainers",
    maintainersTitle: "vaBench release maintainers",
    maintainersBody: "Own the public denominator, task metadata, score roster, and report exports.",
    taskAuthorsEyebrow: "Task authors",
    taskAuthorsTitle: "Benchmark task contributors",
    taskAuthorsBody: "Contribute prompts, gold Verilog-A, checkers, and Spectre/EVAS validation evidence.",
    evaluatorContributorsEyebrow: "Evaluator",
    evaluatorContributorsTitle: "EVAS and Spectre harness contributors",
    evaluatorContributorsBody: "Maintain the fast evaluator, dual-judge runner, bridge scripts, and parity regressions.",
    citationTitle: "Citation",
    citationBody: "Replace this block with the paper citation once the benchmark release is frozen.",
    thRank: "Rank",
    thModel: "Model",
    thProvider: "Provider",
    thDate: "Date",
    thScore: "Score",
    thJudge: "Judge",
    thArtifact: "Artifact",
    thStatus: "Status",
    thEVAS: "EVAS",
    thSpectre: "Spectre",
    thCategory: "Category",
    thEntries: "Entries",
    thRows: "Rows",
    thScoredRows: "Core Score Forms",
    thTask: "Task",
    thForm: "Form",
    thLevel: "Level",
    thBackends: "Backends",
    thParity: "Parity",
    thBackend: "Backend",
    thBehavior: "Behavior",
    thEvidence: "Evidence",
    thClaim: "Claim",
    thActualDifference: "Actual Difference",
    thToleranceGate: "Tolerance Gate",
    thSurface: "Surface",
    thEquivalentRows: "Equivalent Rows",
    thEffectiveMeanRms: "Effective Mean RMS",
    thEffectiveWorstSignalRms: "Effective Worst Signal RMS",
    thRawMeanRms: "Raw Mean RMS",
    thRawWorstSignalRms: "Raw Worst Signal RMS",
    thTaskMetricRows: "Task-Metric Rows",
    thTaskMetricDelta: "Metric Delta",
    thDiagnosticWaveform: "Diagnostic Waveform",
    thDiagnosticMeanRms: "Diagnostic Mean RMS",
    thDiagnosticWorstSignalRms: "Diagnostic Worst Signal RMS",
    thAcceptancePolicy: "Acceptance Policy",
    thReportingRule: "Reporting Rule",
    thMetric: "Metric",
    thValue: "Value",
    thCase: "Case",
    filterSearch: "Search",
    filterCategory: "Category",
    filterForm: "Form",
    filterLevel: "Level",
    filterProvenance: "Provenance",
    filterStatus: "Status",
    filterPolicy: "Policy",
    resetFilters: "Reset",
    taskSearchPlaceholder: "task id, category, function",
    alignmentSearchPlaceholder: "task id, category, policy",
    loadingTaskRows: "Loading task rows...",
    loadingAlignmentRows: "Loading alignment rows...",
    allOption: "All",
    noRowsMatch: "No rows match the current filters.",
    noVerifiedRuns: "No verified model submissions yet.",
    noVerifiedRunsDetail: "Run a model with --final-judge spectre before adding a ranked row.",
    notRanked: "not ranked",
    integrationSmokePassed: "integration smoke passed",
    scorePlotPending: "Awaiting first full Spectre-scored model run",
    scorePlotPendingBody: "The chart appears here after a model completes the 265-form core score roster.",
    scorePlotAxis: "Pass@1",
    smokeTestedModels: "Smoke-tested models",
    smokeEvasShort: "1 row generated/scored; behavior failed",
    connectedModels: "Connected models",
    taskExampleCta: "Open task",
    notRun: "not run",
    generatedScoredFailed: "generated and EVAS-scored 1 row; candidate failed behavior correctness",
    listRoster: "list roster",
    evasOnlyBaseline: "EVAS-only baseline",
    fullEvalWithSpectre: "full eval with Spectre",
    rowsShown: "{shown} of {total} rows shown",
    alignmentRowsShown: "{shown} of {total} alignment rows shown",
    rowsWithRate: "{passed} / {total} rows ({rate})",
    missingCheckers: "{count} missing checkers",
    certified: "certified",
    notCertified: "not certified",
    staticBackend: "static",
    evasBackend: "EVAS",
    spectreBackend: "Spectre",
    spectreRef: "Spectre ref",
    spectreAx: "Spectre AX",
    evasRust: "EVAS Rust",
    evasPython: "EVAS Python",
    counted: "counted",
    notCounted: "not counted",
    meanRmsLine: "mean RMS {mean}, worst {worst}",
    gainDeltaLine: "gain delta {delta}",
    acceptanceBasis: "Acceptance basis",
    bitExactEquality: "Bit-exact equality",
    relativeRmsGate: "Relative RMS gate",
    smallAbsoluteGate: "Small absolute gate",
    gainMetricGate: "Gain metric gate",
    pllRows: "PLL rows",
    edgeWindowPolicy: "Edge window policy",
    metricBenchmarkRows: "Benchmark rows",
    metricScoredRows: "Core score forms",
    metricFourBackend: "Four-backend status",
    metricMismatch: "EVAS PASS / Spectre FAIL",
    metricReleaseEntries: "Release entries",
    metricCategories: "Categories",
    metricAlignedRows: "Gold aligned rows",
    metricBitExact: "Bit-exact claim",
    metricBackendCertified: "Certified backends",
    metricFourwayRows: "Precision evidence rows",
    metricEquivalentSurfaces: "Equivalent surfaces",
    metricPrecisionComparisons: "Gate-passed comparisons",
    metricReviewRows: "Rows needing review",
    metricSpectreSelf: "Spectre self-check",
    metricTaskMetricRows: "Task-metric comparisons",
    detailSingleDenominator: "single public management denominator",
    detailModelRoster: "main leaderboard denominator; certified support forms are reported separately",
    detailCertifiedSurfaces: "certified execution surfaces",
    detailAuditedMismatch: "audited mismatch count",
    detailFunctionEntries: "function-level entries behind rows",
    detailFunctionFamilies: "analog and mixed-signal families",
    detailConnectedModels: "smoke-tested or verified model entries",
    detailSpectreAligned: "aligned within stated tolerance gates",
    detailNotAsserted: "not asserted",
    detailNotBitExact: "not a bit-exact promise",
    detailCommonRows: "single public management denominator",
    detailPrecisionRows: "current full-300 common-row evidence",
    detailEquivalentSurfaces: "EVAS Python, EVAS Rust, Spectre AX",
    detailPrecisionComparisons: "surface-row comparisons passed",
    detailReviewRows: "precision rows blocked or needing review",
    detailSpectreSelf: "AX/classic pairs passed",
    detailTaskMetricRows: "accepted by extracted circuit metrics",
    identicalNoTitle: "No bit-exact claim",
    identicalNoBody: "EVAS outputs and Spectre outputs are not claimed to match point-by-point or bit-for-bit.",
    equivalentYesTitle: "Equivalent under gates",
    equivalentYesBody: "On the current full-300 common-row evidence, EVAS Python, EVAS Rust, and Spectre AX pass the Spectre-strict-referenced gates.",
    differenceTitle: "What differs",
    differenceBody: "The remaining numerical differences are mainly solver sampling, event timing, interpolation, edge windows, transition/cross details, and task-metric extraction.",
    toleranceAnchorTitle: "Where tolerance comes from",
    toleranceAnchorBody: "The tolerance is anchored by observed Spectre AX/classic self-consistency, not by an arbitrary decimal precision.",
    pointwiseEyebrow: "Pointwise caveats",
    pointwiseTitle: "Why raw RMS can look larger",
    pointwiseDescription:
      "These notes are intentionally explicit about known limitations. A row can pass the current gate and still expose a real place where EVAS or the checker should improve.",
    taxonomySymptom: "Symptom",
    taxonomyShortcoming: "Current shortcoming",
    taxonomyHandling: "Current handling",
    taxonomyBugSignal: "When this is a bug",
    taxonomyFeedback: "Useful feedback",
    taxonomyRule: "Reporting rule",
    taskMetricEyebrow: "Task-metric rows",
    taskMetricTitle: "Rows not judged by raw pointwise equality",
    taskMetricDescription:
      "Measurement-flow rows can use extracted circuit metrics as the acceptance gate. Click a row to inspect why diagnostic waveform-only RMS is not the score.",
    anchorComparedPairs: "Compared pairs",
    anchorPassedPairs: "Passed pairs",
    anchorNeedsReviewPairs: "Needs review pairs",
    anchorRowMeanMax: "Row mean relative RMS max",
    anchorWorstSignalMax: "Worst-signal relative RMS max",
    anchorMaxPointAbs: "Max point absolute voltage",
    viewDetails: "View details",
    viewAccuracyCase: "View case",
    sourceUnavailable: "not listed",
    yes: "yes",
    no: "no",
    labelReleaseEntry: "Release entry",
    labelTaskId: "Task id",
    labelLegacyTaskId: "Legacy task id",
    labelIdNamespace: "ID namespace",
    labelBaseFunction: "Base function",
    labelCategory: "Category",
    labelForm: "Form",
    labelLevel: "Level",
    labelDifficulty: "Difficulty",
    labelTrack: "Track",
    labelFamily: "Family",
    labelProvenance: "Provenance",
    labelScoreSurface: "Counted in score",
    labelContentDenominator: "In content denominator",
    labelGoldCount: "Gold assets",
    labelPromptPath: "Prompt",
    labelChecksPath: "Checks",
    labelMetaPath: "Meta",
    labelReleaseManifestPath: "Release task",
    labelEvidencePath: "Evidence",
    labelStatic: "Static",
    labelEvas: "EVAS",
    labelSpectre: "Spectre",
    labelVerdict: "Verdict",
    labelParityStatus: "Parity status",
    labelParityPolicy: "Parity policy",
    labelSourceEquivalence: "Source equivalence",
    labelSignalsCompared: "Signals compared",
    labelSamples: "Samples",
    labelMeanRms: "Mean relative RMS",
    labelWorstRms: "Worst relative RMS",
    labelMaxRmse: "Max RMSE",
    labelMaxAbs: "Max absolute voltage",
    labelDigitalMismatch: "Digital mismatch ratio",
    labelRelativeGainDelta: "Relative gain delta",
    labelAlignmentStatus: "Alignment status",
    labelEqualityClaim: "Equality claim",
    labelMetricFamily: "Metric family",
    labelSimilarity: "Similarity",
    labelTolerance: "Tolerance",
    labelWaveformStatus: "Waveform status",
    labelCandidate: "Candidate",
    labelCandidateGain: "Candidate gain",
    labelReferenceGain: "Reference gain",
    labelDiagnosticNote: "Diagnostic note",
    loadError:
      "Could not load vaBench site data. Run python3 runners/export_vabench_eval_framework.py, python3 runners/export_vabench_github_pages.py, and python3 runners/export_vabench_precision_overview.py, then serve docs/ over HTTP. {message}",
  },
  zh: {
    brandSubtitle: "行为级 Verilog-A 基准",
    navHome: "首页",
    navLeaderboard: "排行榜",
    navBenchmark: "Benchmark",
    navRunModels: "运行模型",
    navProtocol: "协议",
    navAccuracy: "精度",
    navNews: "更新",
    navContributors: "贡献者",
    navBlog: "Blog",
    navRun: "Run",
    navData: "Data",
    navGithub: "GitHub",
    languageToggle: "English",
    languageToggleAria: "切换为英文界面",
    footerGenerated: "由 vaBench release reports 生成。",
    homeEyebrow: "行为级 Verilog-A 评测",
    homeTitle: "vaBench 300",
    homeText:
      "用 EVAS fast gates 和 Spectre final judging 评测 frontier models 在 analog 和 mixed-signal behavioral Verilog-A 任务上的表现。",
    homePrimaryAction: "运行 vaBench",
    homeSecondaryAction: "浏览数据",
    featureBenchmarkEyebrow: "Benchmark",
    featureBenchmarkTitle: "300 个已认证题型",
    featureBenchmarkBody: "按类别、层级、表单、计分面和来源浏览题目。",
    featureLeaderboardEyebrow: "排行榜",
    featureLeaderboardTitle: "Spectre final judge",
    featureLeaderboardBody: "区分 Spectre 计分的 verified runs 和接入 smoke tests。",
    featureProtocolEyebrow: "协议",
    featureProtocolTitle: "EVAS/Spectre gates",
    featureProtocolBody: "查看四后端认证、golden alignment 和容差规则。",
    featureAccuracyEyebrow: "精度",
    featureAccuracyTitle: "精度证据",
    featureAccuracyBody: "查看 EVAS 与 Spectre 是完全相同、gate 内等价，还是存在数值差异。",
    homeLeaderboardEyebrow: "排行榜",
    homeLeaderboardTitle: "排行榜",
    homeLeaderboardBody:
      "Verified rows 需要 Spectre final judge。仅 EVAS 的运行和 API smoke tests 会作为接入证据展示，不进入正式 ranked benchmark score。",
    homeLeaderboardFootnote:
      "主排行榜分母是 265 个核心计分题型；35 个已认证 support 题型单独报告。",
    leaderboardVersionCurrent: "v300",
    leaderboardVersionCore: "核心计分",
    leaderboardVersionSupport: "Support 题型",
    leaderboardMetricScore: "Pass@1",
    leaderboardMetricJudge: "Spectre 判定",
    homeNewsEyebrow: "更新",
    homeNewsTitle: "最近更新",
    viewAllNews: "查看所有更新",
    whyEyebrow: "为什么是 vaBench",
    whyTitle: "为 behavioral circuit modeling 设计",
    whyBody:
      "vaBench 是面向 analog 和 mixed-signal behavioral Verilog-A 生成的公开 benchmark。它把题目内容、参考产物、确定性 checker、EVAS 快速 gate 和 Spectre final judge 作为分开的证据公开展示。",
    taskExamplesEyebrow: "题目示例",
    taskExamplesTitle: "vaBench 300 中的部分题目",
    taskExamplesBody:
      "每个示例都能打开原始题面、参考产物、checker contract、认证状态和 EVAS/Spectre 精度证据。",
    viewAllTasks: "查看全部 300 题",
    homeReadEyebrow: "阅读协议",
    homeReadTitle: "vaBench 如何计分和认证",
    homeReadBody:
      "协议把公开 benchmark 题目、核心计分题型、support 题型、EVAS 快速 gate、Spectre final judge 和容差等价证据分开说明。",
    homeReadProtocol: "打开协议",
    homeReadAccuracy: "查看精度",
    leaderboardEyebrow: "排行榜",
    leaderboardPageTitle: "vaBench 模型排行榜",
    leaderboardPageText:
      "Verified rows 需要 Spectre 最终判定。EVAS-only runs 和 API smoke tests 只作为接入证据展示，不作为正式排行分数。",
    verifiedRunsEyebrow: "Verified runs",
    verifiedRunsTitle: "Spectre 计分提交",
    verifiedRunsDescription: "只有模型使用 Spectre final judge 跑完 scored roster 后，才会进入这张表。",
    integrationEyebrow: "接入状态",
    integrationTitle: "已 smoke-test 的模型访问",
    submitRunTitle: "提交或复现一次运行",
    submitRunText: "先使用统一 runner。结果可排名时发布顶层 summary。",
    benchmarkEyebrow: "Benchmark",
    benchmarkPageTitle: "vaBench 300 题目集",
    benchmarkPageText:
      "按功能族、任务表单、层级、难度和计分面浏览 benchmark。公开管理分母是 300 行；当前核心计分 roster 是 265 个题型，另有 35 个已认证 support 题型单独报告。",
    coverageEyebrow: "覆盖",
    coverageTitle: "功能类别",
    coverageDescription: "模拟与混合信号行为功能族的 entry 和 row 覆盖。",
    taskGalleryEyebrow: "题目列表",
    taskGalleryTitle: "Released rows",
    taskGalleryDescription: "搜索和筛选 300 行。点击题目名可以查看公开资产、后端状态和精度证据。",
    idGuideTitle: "ID 说明",
    idGuideVbr1: "vaBench release v1 继承 entry 的命名空间；不是数量、排名或分数。",
    idGuideVbr11: "vaBench v1.1 promoted entry 的历史写法，表示后来补进 300-row surface 的题。",
    idGuideLevel: "benchmark 层级：可复用功能行与组合 flow 行。",
    idGuideForm: "同一个 entry 下的 form 后缀；这些 form 才是 300-row 分母里的 row。",
    benchmarkDetailEyebrow: "Benchmark 详情",
    benchmarkDetailTitle: "单题详情",
    benchmarkDetailText:
      "查看一个 released row 的题目身份、benchmark 内容、认证状态和 EVAS/Spectre 精度证据。",
    taskDetailBack: "返回 benchmark",
    taskDetailMissing: "没有找到这道题",
    taskDetailMissingBody: "当前 URL 没有匹配到 released vaBench row。请回到 benchmark 表格，从某一行点进来。",
    taskDetailIdentityTitle: "题目身份",
    taskDetailAssetsTitle: "公开资产",
    taskDetailEvaluationTitle: "认证与 parity",
    taskDetailPrecisionTitle: "精度证据",
    taskDetailContentsEyebrow: "Benchmark 内容",
    taskDetailContentsTitle: "核心 benchmark 文件",
    taskDetailContentsDescription:
      "优先查看人工审查最需要的四类文件：题面、参考答案、参考 testbench、评测 checks。Metadata 和 manifest 放在下方高级原始文件区。",
    taskDetailNoContents: "这行没有可内嵌展示的 benchmark 内容。",
    taskDetailCorePromptTitle: "题面",
    taskDetailCorePromptBody: "模型提交时看到的原始公开 prompt。",
    taskDetailCoreAnswerTitle: "参考答案",
    taskDetailCoreAnswerBody: "作为参考实现的 gold Verilog-A 源文件。多模块 e2e 行可能包含多个源文件。",
    taskDetailCoreTestbenchTitle: "参考 testbench",
    taskDetailCoreTestbenchBody: "用于驱动参考实现的 Spectre testbench 文件。",
    taskDetailCoreEvaluationTitle: "评测 checks",
    taskDetailCoreEvaluationBody: "机器可读 checker contract，包括语法、编译、仿真正确性和 parity。",
    taskDetailCoreSuppliedTitle: "题目输入/支持文件",
    taskDetailCoreSuppliedBody: "属于任务上下文的原始输入或支持文件，例如 bugfix 行里的 buggy source。",
    taskDetailAdvancedTitle: "高级原始文件",
    taskDetailAdvancedDescription: "用于审计和 runner 集成的机器 metadata 与完整 raw export 文件。",
    taskDetailAccuracyCasesTitle: "相关精度案例",
    taskDetailNoAccuracyCase: "这行没有记录 task-metric 精度案例。",
    openPrompt: "打开 prompt",
    openChecks: "打开 checks",
    openMeta: "打开 meta",
    openReleaseManifest: "打开 release task",
    openEvidence: "打开 evidence",
    openSource: "打开源码",
    fileMissing: "网站导出中没有找到这个文件。",
    fileTruncated: "网站导出中已截断。",
    fileBytes: "{count} bytes",
    contentKindPrompt: "Prompt",
    contentKindChecks: "Checker",
    contentKindMeta: "Metadata",
    contentKindReleaseTask: "Release task",
    contentKindGold: "Gold/reference artifact",
    contentKindReferenceAnswer: "参考答案",
    contentKindReferenceTestbench: "参考 testbench",
    contentKindSuppliedArtifact: "题目输入/支持文件",
    protocolEyebrow: "协议",
    protocolPageTitle: "评测与认证 gate",
    protocolPageText:
      "Spectre 是最终判定。EVAS 是快速 evaluator，但必须在支持的 voltage-domain/event-driven 子集上保持与 Spectre 对齐。",
    backendCertificationEyebrow: "后端认证",
    backendCertificationTitle: "四个执行面",
    backendCertificationDescription: "这些行认证 benchmark 和 evaluator 表面，不是模型排行榜结果。",
    claimBoundaryEyebrow: "结论边界",
    claimBoundaryTitle: "可以声称什么",
    parityGatesEyebrow: "Parity gates",
    alignmentEyebrow: "Spectre 对齐",
    alignmentTitle: "Golden reference 等价表",
    alignmentDescription:
      "每行说明比较了什么、EVAS/Spectre 实际差异以及使用哪个容差 gate。不宣称 bit-exact 完全一致。",
    accuracyEyebrow: "精度",
    accuracyPageTitle: "EVAS 与 Spectre 精度",
    accuracyPageText:
      "benchmark 不声称 bit-exact 完全一致；它报告各执行面是否在明确 gate 下与 Spectre reference 行为等价。",
    accuracyCaseEyebrow: "精度案例",
    accuracyCaseTitle: "单个精度案例详情",
    accuracyCaseText:
      "查看一个 task-metric 精度案例，以及为什么这里的 raw pointwise RMS 只是诊断信息而不是接受分数。",
    accuracyCaseBack: "返回精度页",
    accuracyCaseMissing: "没有找到这个精度案例",
    accuracyCaseMissingBody: "当前 URL 没有匹配到已记录的 task-metric 精度行。请从 Accuracy 表格点进来。",
    accuracyCaseMetricsTitle: "案例指标",
    accuracyCaseTaskTitle: "关联 benchmark row",
    accuracyCaseWhyTitle: "为什么这里 raw RMS 可能较大",
    accuracyCaseWhyText:
      "这些说明用于阅读当前案例：解释为什么当前 gate 接受这行，也诚实标出 EVAS 或 checker 仍可改进的地方。",
    accuracyCaseTaskLink: "打开 benchmark row",
    accuracyIdenticalEyebrow: "等价结论",
    accuracyIdenticalTitle: "输出是否完全一致？",
    accuracyTermsEyebrow: "如何理解容差",
    accuracyTermsTitle: "Gate 具体约束什么",
    precisionStrictEyebrow: "四路参考",
    precisionStrictTitle: "相对 Spectre strict 的精度",
    precisionStrictDescription:
      "EVAS Python、EVAS Rust 和 Spectre AX 都在当前 full-300 common-row 集合上与 Spectre strict reference 比较。",
    spectreAnchorEyebrow: "容差锚点",
    spectreAnchorTitle: "Spectre AX vs classic",
    spectreAnchorDescription:
      "Spectre 官方两种模式本身也不是 bit-identical。这份自一致性报告用于锚定哪些 waveform drift 在判定 EVAS mismatch 前是可接受的。",
    newsEyebrow: "更新",
    newsPageTitle: "更新与 release notes",
    newsPageText: "用一条人类可读时间线追踪 benchmark、evaluator、runner 和文档变化。",
    contributorsEyebrow: "贡献者",
    contributorsPageTitle: "人员与引用",
    contributorsPageText: "用于放置 benchmark 维护者、任务作者、evaluator 贡献者和引用说明。",
    maintainersEyebrow: "维护者",
    maintainersTitle: "vaBench release 维护者",
    maintainersBody: "维护公开分母、任务元数据、score roster 和报告导出。",
    taskAuthorsEyebrow: "任务作者",
    taskAuthorsTitle: "Benchmark 题目贡献者",
    taskAuthorsBody: "贡献 prompts、gold Verilog-A、checkers 以及 Spectre/EVAS 验证证据。",
    evaluatorContributorsEyebrow: "Evaluator",
    evaluatorContributorsTitle: "EVAS 与 Spectre harness 贡献者",
    evaluatorContributorsBody: "维护快速 evaluator、dual-judge runner、bridge scripts 和 parity regressions。",
    citationTitle: "引用",
    citationBody: "benchmark release 冻结后，把这里替换成论文引用。",
    thRank: "排名",
    thModel: "模型",
    thProvider: "服务商",
    thDate: "日期",
    thScore: "分数",
    thJudge: "裁判",
    thArtifact: "产物",
    thStatus: "状态",
    thEVAS: "EVAS",
    thSpectre: "Spectre",
    thCategory: "类别",
    thEntries: "Entries",
    thRows: "行数",
    thScoredRows: "核心计分题型",
    thTask: "题目",
    thForm: "表单",
    thLevel: "层级",
    thBackends: "后端",
    thParity: "Parity",
    thBackend: "后端",
    thBehavior: "行为结果",
    thEvidence: "证据",
    thClaim: "结论",
    thActualDifference: "实际差异",
    thToleranceGate: "容差 Gate",
    thSurface: "执行面",
    thEquivalentRows: "等价行",
    thEffectiveMeanRms: "有效平均 RMS",
    thEffectiveWorstSignalRms: "有效最差信号 RMS",
    thRawMeanRms: "原始平均 RMS",
    thRawWorstSignalRms: "原始最差信号 RMS",
    thTaskMetricRows: "Task-metric 行",
    thTaskMetricDelta: "指标差异",
    thDiagnosticWaveform: "诊断波形",
    thDiagnosticMeanRms: "诊断平均 RMS",
    thDiagnosticWorstSignalRms: "诊断最差信号 RMS",
    thAcceptancePolicy: "接受策略",
    thReportingRule: "报告规则",
    thMetric: "指标",
    thValue: "值",
    thCase: "案例",
    filterSearch: "搜索",
    filterCategory: "类别",
    filterForm: "表单",
    filterLevel: "层级",
    filterProvenance: "来源",
    filterStatus: "状态",
    filterPolicy: "策略",
    resetFilters: "重置",
    taskSearchPlaceholder: "task id、类别、功能",
    alignmentSearchPlaceholder: "task id、类别、策略",
    loadingTaskRows: "正在加载题目行...",
    loadingAlignmentRows: "正在加载对齐行...",
    allOption: "全部",
    noRowsMatch: "当前筛选条件下没有匹配行。",
    noVerifiedRuns: "还没有 verified model submissions。",
    noVerifiedRunsDetail: "模型需要用 --final-judge spectre 跑完后，才加入排行。",
    notRanked: "不排名",
    integrationSmokePassed: "接入 smoke 通过",
    scorePlotPending: "等待第一次完整 Spectre 计分模型运行",
    scorePlotPendingBody: "模型跑完 265 个核心计分题型后，图表会显示在这里。",
    scorePlotAxis: "Pass@1",
    smokeTestedModels: "Smoke-tested 模型",
    smokeEvasShort: "已生成/评分 1 行；行为未通过",
    connectedModels: "已接入模型",
    taskExampleCta: "打开题目",
    notRun: "未运行",
    generatedScoredFailed: "已生成并用 EVAS 评分 1 行；候选行为正确性失败",
    listRoster: "查看名单",
    evasOnlyBaseline: "仅 EVAS baseline",
    fullEvalWithSpectre: "完整评测含 Spectre",
    rowsShown: "当前显示 {shown} / {total} 行",
    alignmentRowsShown: "当前显示 {shown} / {total} 个对齐行",
    rowsWithRate: "{passed} / {total} 行 ({rate})",
    missingCheckers: "{count} 行缺少 checker",
    certified: "已认证",
    notCertified: "未认证",
    staticBackend: "静态",
    evasBackend: "EVAS",
    spectreBackend: "Spectre",
    spectreRef: "Spectre ref",
    spectreAx: "Spectre AX",
    evasRust: "EVAS Rust",
    evasPython: "EVAS Python",
    counted: "计分",
    notCounted: "不计分",
    meanRmsLine: "平均 RMS {mean}，最差 {worst}",
    gainDeltaLine: "增益差 {delta}",
    acceptanceBasis: "接受依据",
    bitExactEquality: "Bit-exact 完全相同",
    relativeRmsGate: "相对 RMS gate",
    smallAbsoluteGate: "小绝对误差 gate",
    gainMetricGate: "增益指标 gate",
    pllRows: "PLL 行",
    edgeWindowPolicy: "边沿窗口策略",
    metricBenchmarkRows: "Benchmark 行数",
    metricScoredRows: "核心计分题型",
    metricFourBackend: "四后端状态",
    metricMismatch: "EVAS PASS / Spectre FAIL",
    metricReleaseEntries: "Release entries",
    metricCategories: "类别",
    metricAlignedRows: "Gold 对齐行",
    metricBitExact: "Bit-exact 声称",
    metricBackendCertified: "认证后端",
    metricFourwayRows: "精度证据行",
    metricEquivalentSurfaces: "等价执行面",
    metricPrecisionComparisons: "Gate 通过比较",
    metricReviewRows: "待复核行",
    metricSpectreSelf: "Spectre 自检",
    metricTaskMetricRows: "Task-metric 比较",
    detailSingleDenominator: "统一公开管理分母",
    detailModelRoster: "主排行榜分母；已认证 support 题型单独报告",
    detailCertifiedSurfaces: "已认证执行面",
    detailAuditedMismatch: "已审计 mismatch 数",
    detailFunctionEntries: "行背后的功能级 entries",
    detailFunctionFamilies: "模拟与混合信号功能族",
    detailConnectedModels: "已 smoke-test 或 verified 的模型接入",
    detailSpectreAligned: "在所列容差 gate 内对齐",
    detailNotAsserted: "不宣称",
    detailNotBitExact: "不承诺 bit-exact",
    detailCommonRows: "统一公开管理分母",
    detailPrecisionRows: "当前 full-300 common-row 证据",
    detailEquivalentSurfaces: "EVAS Python、EVAS Rust、Spectre AX",
    detailPrecisionComparisons: "surface-row 比较通过数",
    detailReviewRows: "blocked 或 needs-review 的精度行",
    detailSpectreSelf: "AX/classic 通过的 pair",
    detailTaskMetricRows: "由提取出的电路指标接受",
    identicalNoTitle: "不声称 bit-exact",
    identicalNoBody: "EVAS 输出和 Spectre 输出不主张逐点或逐 bit 完全相同。",
    equivalentYesTitle: "在 gate 内等价",
    equivalentYesBody: "在当前 full-300 common-row 证据上，EVAS Python、EVAS Rust 和 Spectre AX 都通过了以 Spectre strict 为 reference 的 gate。",
    differenceTitle: "差别主要是什么",
    differenceBody: "剩余数值差异主要来自 solver 采样、event timing、插值、边沿窗口、transition/cross 细节以及任务指标提取方式。",
    toleranceAnchorTitle: "容差从哪里来",
    toleranceAnchorBody: "容差由 Spectre AX/classic 自一致性中的可观测漂移锚定，不是随意设定的小数位精度。",
    pointwiseEyebrow: "逐点差异说明",
    pointwiseTitle: "为什么 raw RMS 可能更大",
    pointwiseDescription:
      "这里会刻意写出现有不足：某一行通过当前 gate，并不代表 EVAS 或 checker 已经没有可改进空间。",
    taxonomySymptom: "现象",
    taxonomyShortcoming: "当前不足",
    taxonomyHandling: "现有处理",
    taxonomyBugSignal: "什么时候算 bug",
    taxonomyFeedback: "希望收到的反馈",
    taxonomyRule: "报告规则",
    taskMetricEyebrow: "Task-metric 行",
    taskMetricTitle: "不是用 raw pointwise equality 判定的行",
    taskMetricDescription:
      "测量流程类 row 可以用提取出的电路指标作为接受 gate。点击某一行可以查看为什么诊断 waveform-only RMS 不是 score。",
    anchorComparedPairs: "比较 pair",
    anchorPassedPairs: "通过 pair",
    anchorNeedsReviewPairs: "待复核 pair",
    anchorRowMeanMax: "行平均相对 RMS 最大值",
    anchorWorstSignalMax: "最差信号相对 RMS 最大值",
    anchorMaxPointAbs: "最大点绝对电压",
    viewDetails: "查看详情",
    viewAccuracyCase: "查看案例",
    sourceUnavailable: "未列出",
    yes: "是",
    no: "否",
    labelReleaseEntry: "Release entry",
    labelTaskId: "Task id",
    labelLegacyTaskId: "Legacy task id",
    labelIdNamespace: "ID 命名空间",
    labelBaseFunction: "基础功能",
    labelCategory: "类别",
    labelForm: "表单",
    labelLevel: "层级",
    labelDifficulty: "难度",
    labelTrack: "Track",
    labelFamily: "Family",
    labelProvenance: "来源",
    labelScoreSurface: "是否计分",
    labelContentDenominator: "是否进入内容分母",
    labelGoldCount: "Gold 资产数",
    labelPromptPath: "Prompt",
    labelChecksPath: "Checks",
    labelMetaPath: "Meta",
    labelReleaseManifestPath: "Release task",
    labelEvidencePath: "Evidence",
    labelStatic: "Static",
    labelEvas: "EVAS",
    labelSpectre: "Spectre",
    labelVerdict: "Verdict",
    labelParityStatus: "Parity 状态",
    labelParityPolicy: "Parity 策略",
    labelSourceEquivalence: "Source equivalence",
    labelSignalsCompared: "比较信号数",
    labelSamples: "采样点",
    labelMeanRms: "平均相对 RMS",
    labelWorstRms: "最差相对 RMS",
    labelMaxRmse: "最大 RMSE",
    labelMaxAbs: "最大绝对电压",
    labelDigitalMismatch: "数字 mismatch 比例",
    labelRelativeGainDelta: "相对增益差",
    labelAlignmentStatus: "Alignment 状态",
    labelEqualityClaim: "Equality 声称",
    labelMetricFamily: "Metric family",
    labelSimilarity: "相似度",
    labelTolerance: "容差",
    labelWaveformStatus: "Waveform 状态",
    labelCandidate: "候选执行面",
    labelCandidateGain: "候选 gain",
    labelReferenceGain: "Reference gain",
    labelDiagnosticNote: "诊断说明",
    loadError:
      "无法加载 vaBench 网站数据。请运行 python3 runners/export_vabench_eval_framework.py、python3 runners/export_vabench_github_pages.py 和 python3 runners/export_vabench_precision_overview.py，然后通过 HTTP 服务打开 docs/。{message}",
  },
};

const CATEGORY_LABELS_ZH = {
  "Baseband Signal Conditioning": "基带信号调理",
  "Bias Reference and Power Management": "偏置、基准与电源管理",
  "Calibration, DEM, and Control": "校准、DEM 与控制",
  "Comparator and Decision Circuits": "比较器与判决电路",
  "Data Converter Models": "数据转换器模型",
  "Measurement Instrumentation Flows": "测量仪表流程",
  "PLL Clock and Timing Systems": "PLL、时钟与时序系统",
  "RF and AFE Behavioral Macromodels": "RF 与 AFE 行为宏模型",
  "Sampling and Analog Memory": "采样与模拟存储",
  "Stimulus and Source Generators": "激励与源发生器",
};

const PROVENANCE_LABELS_ZH = {
  inherited_v1: "v1 继承",
  "promoted_v1.1": "v1.1 新增",
};

const POLICY_LABELS_ZH = {
  full_300_closure: "full-300 闭环",
  spectre_equivalence_core_v1: "Spectre 等价 core v1",
  spectre_equivalence_core_v2: "Spectre 等价 core v2",
  gain_metric: "增益指标",
  gain_extraction_metric_parity_v1: "增益指标 parity",
  pll_task_aware: "PLL task-aware",
};

const STATUS_LABELS_ZH = {
  pass: "通过",
  passed: "通过",
  ready: "就绪",
  certified: "已认证",
  true: "通过",
  false: "未通过",
  fail: "失败",
  failed: "失败",
  error: "错误",
  pending: "待处理",
  missing: "缺失",
  partial: "部分完成",
  score_enabled: "计分启用",
  spectre_aligned_within_tolerance: "Spectre 容差内一致",
  integration_smoke_passed: "接入 smoke 通过",
  equivalent_to_spectre_strict: "等价",
  needs_review: "待复核",
};

const GATE_LABELS_ZH = {
  behavior_checker: "行为 checker",
  relative_waveform: "相对 waveform RMS",
  small_absolute_voltage: "小绝对电压误差",
  edge_window: "边沿/不连续窗口",
  task_metric: "任务指标",
};

const GATE_MEANINGS_ZH = {
  behavior_checker: "电路级功能正确性是主要接受信号。",
  relative_waveform: "只有归一化 RMS 误差保持在 gate 内，逐点波形差异才被接受。",
  small_absolute_voltage: "当信号幅度很小导致相对误差被放大时，可由绝对电压误差 gate 接受。",
  edge_window: "不连续点附近的 solver 采样差异不直接视为功能 mismatch，前提是稳定区匹配。",
  task_metric: "部分行使用提取出的电路指标判定，而不是逐点 waveform equality。",
};

const TAXONOMY_ZH = {
  solver_sampling_grid: {
    label: "Solver 采样网格",
    what_changes: "EVAS 和 Spectre 可能保存不同的 transient accepted steps，因此报告会在重采样后的共同网格上比较共同信号。",
    why_expected: "自适应求解器即使得到等价的电路轨迹，也可能选择不同的输出点。",
    known_shortcoming: "我们的比较不能证明 EVAS 复现了 Spectre 的内部 accepted-step 历史；它只比较对齐后的可观测保存信号。",
    current_handling: "当前报告使用固定共同采样网格，同时保留 effective RMS 和 raw RMS。",
    bug_signal: "如果稳定区域不一致、checker 结果改变，或者某行只能通过隐藏很宽的时间区间才能通过，就应该当作 bug。",
    feedback_wanted: "请提供 row id、两份 CSV trace，以及对齐后稳定区域首次明显偏离的时间范围。",
    reporting_rule: "把 aligned-grid RMS 当作诊断指标；不要解读为 bit-exact 完全一致。",
  },
  event_time_and_cross: {
    label: "事件时间与 cross() 定位",
    what_changes: "cross() 事件和 timer 事件可能在略有不同的局部时间触发。",
    why_expected: "两个引擎的 event scheduling 和 breakpoint localization 机制不同。",
    known_shortcoming: "EVAS 还没有声称覆盖所有 Spectre 等价的 cross()、timer()、transition() 和 simultaneous-event corner case 排序语义。",
    current_handling: "事件密集的 row 先由 behavior checker 判定，再在支持子集内用 waveform/event diagnostics 检查。",
    bug_signal: "如果边沿漏触发、重复触发、状态更新顺序改变，或出现 EVAS PASS / Spectre FAIL，就应该当作 bug。",
    feedback_wanted: "最有价值的是能触发问题的最小 Verilog-A 片段，尤其是相关 cross()/timer() 语句。",
    reporting_rule: "先检查 behavior、event consistency 和 edge-window 指标，再判断是否 mismatch。",
  },
  edge_window: {
    label: "边沿与不连续窗口",
    what_changes: "快速边沿、不连续点或数字阈值附近的少数采样点可能主导 raw pointwise error。",
    why_expected: "一个采样点的边沿位置差异可能产生很大的瞬时电压差，但稳定区域仍匹配。",
    known_shortcoming: "edge-window 是务实的 acceptance gate；如果使用不谨慎，可能掩盖真实的 timing 或 threshold bug。",
    current_handling: "effective metrics 只允许扣除有界的局部窗口；raw metrics 会并排保留用于审计。",
    bug_signal: "如果被排除窗口变宽、在多次边沿反复出现、改变采样判决，或影响 task metric，就应该当作 bug。",
    feedback_wanted: "请报告信号名、边沿时间、raw max error，以及边沿后的状态或 checker 输出是否改变。",
    reporting_rule: "effective metrics 可以扣除有界局部窗口；raw metrics 仍然保留用于审计。",
  },
  interpolation: {
    label: "共同网格插值",
    what_changes: "保存的 waveform 会先插值，再做 RMS 比较。",
    why_expected: "原始输出时间不同，必须插值后才能逐点比较。",
    known_shortcoming: "当前诊断使用简单共同网格插值；对稀疏输出和很尖锐的 transition，误差可能被放大或缩小。",
    current_handling: "我们报告 row-level 和 worst-signal RMS，而不是用一个单一 pass/fail 标量隐藏插值敏感性。",
    bug_signal: "如果更密的 save grid 或直接 event-time 比较会改变某行结论，就应该当作需要修复的问题。",
    feedback_wanted: "如果有更好的比较方法，或发现某行会因为插值选择而翻转结果，请直接指出。",
    reporting_rule: "把插值误差视为精度诊断的一部分，而不是任务功能分数。",
  },
  transition_smoothing: {
    label: "transition() 平滑",
    what_changes: "transition() ramp 的 breakpoint 位置和采样斜率可能略有不同。",
    why_expected: "EVAS 和 Spectre 不承诺内部平滑调度完全一致。",
    known_shortcoming: "EVAS 的 transition 处理只对 benchmark 支持的 case 做了对齐，不是 Spectre 内部 smoothing 实现的完整公开克隆。",
    current_handling: "稳定区行为、checker 结果、raw/effective waveform metrics 会一起展示，避免 transition artifact 被静默忽略。",
    bug_signal: "如果 transition delay、rise/fall time 或 target update 语义改变下游判决或指标，就应该当作 bug。",
    feedback_wanted: "最有帮助的是小型 transition() 例子，包含期望时序、target update 和保存 waveform。",
    reporting_rule: "当 transition 边沿抬高 raw RMS 时，应检查稳定区行为和 checker 指标。",
  },
  noise_like_or_dithered_stimulus: {
    label: "噪声式或 dither 激励",
    what_changes: "带 dither、伪随机控制或测量激励的 row，可能逐点相位不一致，但提取出的电路指标仍一致。",
    why_expected: "这些 row 的设计目标通常是 gain、lock、count 或 convergence 等聚合指标，不是 sample-by-sample 噪声相位相同。",
    known_shortcoming: "如果 checker metric 过宽，可能漏掉电路设计者关心的 waveform-level 差异。",
    current_handling: "页面把 task-metric rows 单独列出，并保留同一行的 diagnostic waveform-only RMS。",
    bug_signal: "如果换 seed、window 或 stimulus phase 会改变 pass/fail，或者聚合指标掩盖明显功能漂移，就应该当作 bug。",
    feedback_wanted: "欢迎给出更强的 metric window、确定性 seed 或额外 observable 建议。",
    reporting_rule: "用确定性的 task metric 作为 acceptance gate，同时把 pointwise RMS 作为辅助证据。",
  },
  task_metric_gate: {
    label: "Task-metric gate",
    what_changes: "部分 row 用提取出的电路指标接受，例如 gain、lock 或 frequency，而不是 raw pointwise waveform equality。",
    why_expected: "测量流程类任务可能使用 dither/noise-like stimulus，逐点相位不是设计目标。",
    known_shortcoming: "task-metric gate 的质量取决于 checker。checker 太弱会过度接受；太紧又可能误拒有效的 simulator 差异。",
    current_handling: "报告会并排展示 task-metric policy、metric delta、diagnostic waveform status 和 raw/effective RMS。",
    bug_signal: "如果 metric tolerance 没有文档、metric 不具备电路意义，或 waveform 明显错误但 row 仍通过，就应该当作 bug。",
    feedback_wanted: "欢迎给出具体 checker 改进：额外 observable、更好的窗口、更严格的 metric bounds 或 task-specific edge cases。",
    reporting_rule: "报告 task metric，同时只把 pointwise waveform diagnostics 作为解释上下文。",
  },
};

const state = {
  language: localStorage.getItem(LANGUAGE_KEY) === "zh" ? "zh" : "en",
  payloads: {},
  tasks: [],
  alignment: [],
  taskFiltersReady: false,
  alignmentFiltersReady: false,
};

function t(key) {
  return I18N[state.language]?.[key] || I18N.en[key] || key;
}

function format(key, values) {
  return t(key).replace(/\{(\w+)\}/g, (_, name) => values[name] ?? "");
}

function locale() {
  return state.language === "zh" ? "zh-CN" : "en-US";
}

function text(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function number(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return Number.isInteger(value) ? value.toLocaleString(locale()) : value.toPrecision(3);
  }
  return String(value);
}

function preciseNumber(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    if (value === 0) {
      return "0";
    }
    if (Math.abs(value) >= 1000 || Math.abs(value) < 0.001) {
      return value.toExponential(3);
    }
    return value.toPrecision(6);
  }
  return String(value);
}

function percent(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "-";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function byId(id) {
  return document.getElementById(id);
}

function make(tag, className, content) {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (content !== undefined) {
    element.textContent = content;
  }
  return element;
}

function translated(value) {
  const output = text(value);
  if (state.language !== "zh") {
    const englishMap = {
      not_asserted: "not asserted",
      spectre_aligned_within_tolerance: "Spectre-aligned within tolerance",
      waveform_relative_rms_and_absolute_voltage: "waveform RMS and absolute-voltage parity",
      extracted_gain_metric: "extracted gain metric",
      gain_extraction_metric_parity_v1: "gain extraction metric parity",
      pll_task_level_lock_frequency_control: "PLL lock/frequency/control task metric",
    };
    return englishMap[output] || output;
  }
  const map = {
    "not_asserted": "不宣称",
    "gain_extraction_metric_parity_v1": "增益提取指标 parity",
    "not bit-exact; equivalent within the stated acceptance gate": "不是 bit-exact；在所列 acceptance gate 内等价",
    "gold EVAS transient/metric result vs gold Spectre reference result for the same released row":
      "同一 released row 的 gold EVAS transient/metric 结果与 gold Spectre reference 结果",
    "common saved transient waveform columns compared on an aligned sample grid":
      "在对齐采样网格上比较共同保存的 transient waveform columns",
    "EVAS and Spectre extracted gain metric compared instead of pointwise waveform":
      "比较 EVAS 和 Spectre 提取出的 gain metric，而不是逐点波形",
    "task-level PLL lock/frequency/control checker pass, not pointwise waveform equality":
      "通过 task-level PLL lock/frequency/control checker，不主张逐点波形相等",
    "behavior/spec pass plus EVAS/Spectre waveform or task-metric parity":
      "behavior/spec pass 加 EVAS/Spectre waveform 或 task-metric parity",
    "Do not state bit-exact EVAS/Spectre equality; state behavior/spec pass plus tolerance-gated waveform or task-metric parity.":
      "不要声称 EVAS/Spectre bit-exact 完全相同；应表述为 behavior/spec pass 加容差约束下的 waveform 或 task-metric parity。",
    "Claim 300/300 four-backend behavior certification only when backend_coverage.status is pass and every listed full-300 summary remains current.":
      "只有当 backend_coverage.status 为 pass 且所有列出的 full-300 summary 仍为当前证据时，才声称 300/300 四后端行为认证。",
    "Current full-300 backend evidence is grounded by the explicit results/*/summary.json files listed in backend_coverage.":
      "当前 full-300 后端证据以 backend_coverage 中列出的 results/*/summary.json 为准。",
    "Negative candidates are static-shape audited partial-pass assets unless a separate full-checker validation report is produced.":
      "Negative candidates 只是经过 static-shape 审计的 partial-pass 资产，除非另有 full-checker validation report。",
  };
  let result = map[output] || output;
  result = result.replaceAll("row behavior checker PASS under full-300 closure; tolerance is checker-specific", "full-300 闭环下 row behavior checker PASS；容差由 checker 指定");
  result = result.replaceAll("checker-only closure: all four backends passed the row behavior checker; no waveform scalar was materialized for this row", "checker-only 闭环：四个后端都通过 row behavior checker；该行没有物化 waveform scalar");
  result = result.replaceAll("task_checker_status=passed", "task checker=通过");
  result = result.replaceAll("status=passed", "状态=通过");
  result = result.replaceAll("relative_gate PASS", "relative gate 通过");
  result = result.replaceAll("small_absolute_gate PASS", "small absolute gate 通过");
  result = result.replaceAll("relative_gain_delta", "相对增益差");
  result = result.replaceAll("mean_rel_rms", "平均相对 RMS");
  result = result.replaceAll("worst_rel_rms", "最差信号相对 RMS");
  result = result.replaceAll("max_rmse_v", "最大 RMSE");
  result = result.replaceAll("max_abs_v", "最大绝对误差");
  return result;
}

function categoryLabel(value) {
  const original = text(value);
  return state.language === "zh" ? CATEGORY_LABELS_ZH[original] || original : original;
}

function provenanceLabel(value) {
  const original = text(value);
  return state.language === "zh" ? PROVENANCE_LABELS_ZH[original] || original : original;
}

function policyLabel(value) {
  const original = text(value);
  return state.language === "zh" ? POLICY_LABELS_ZH[original] || original : original;
}

function statusLabel(value) {
  const normalized = String(value || "").toLowerCase();
  if (state.language === "zh" && STATUS_LABELS_ZH[normalized]) {
    return STATUS_LABELS_ZH[normalized];
  }
  const englishMap = {
    equivalent_to_spectre_strict: "equivalent",
    needs_review: "needs review",
  };
  if (state.language !== "zh" && englishMap[normalized]) {
    return englishMap[normalized];
  }
  return text(value);
}

function statusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (["pass", "passed", "ready", "certified", "true", "score_enabled", "integration_smoke_passed", "equivalent_to_spectre_strict"].includes(normalized)) {
    return "pass";
  }
  if (["fail", "failed", "false", "error"].includes(normalized)) {
    return "fail";
  }
  if (["pending", "missing", "partial", "not run", "needs_review"].includes(normalized)) {
    return "warn";
  }
  return "";
}

function pill(value, label) {
  const element = make("span", `status ${statusClass(value)}`, label || statusLabel(value));
  element.title = text(value);
  return element;
}

function codeText(value) {
  return make("code", "mono", text(value));
}

function idNamespaceMeaning(entryId) {
  const value = String(entryId || "");
  if (value.startsWith("vbr11_")) {
    return state.language === "zh"
      ? "vaBench v1.1 promoted-entry 命名空间；这是后来补进 300-row benchmark surface 的稳定内部 ID 前缀。"
      : "vaBench v1.1 promoted-entry namespace; a stable internal ID prefix for rows added to the 300-row benchmark surface.";
  }
  if (value.startsWith("vbr1_")) {
    return state.language === "zh"
      ? "vaBench release v1 继承 entry 命名空间；这是稳定内部 ID 前缀，不是数量、排名或分数。"
      : "vaBench release v1 inherited-entry namespace; a stable internal ID prefix, not a count, rank, or score.";
  }
  return state.language === "zh" ? "稳定内部 benchmark ID 命名空间。" : "Stable internal benchmark ID namespace.";
}

function rateBar(value) {
  const wrapper = make("div", "rate-bar");
  const fill = document.createElement("span");
  const clamped = Math.max(0, Math.min(1, typeof value === "number" ? value : 0));
  fill.style.width = `${clamped * 100}%`;
  wrapper.append(fill);
  return wrapper;
}

function ratioText(passed, total) {
  return `${number(passed)} / ${number(total)}`;
}

function queryParam(name) {
  return new URLSearchParams(window.location.search).get(name) || "";
}

function encodedPath(path) {
  return String(path || "")
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function githubSourceHref(path) {
  if (!path) {
    return "";
  }
  return `https://github.com/BucketSran/behavioral-veriloga-eval/blob/main/${encodedPath(path)}`;
}

function taskHref(row) {
  const params = new URLSearchParams();
  params.set("id", row.release_entry_id || row.task_id || "");
  params.set("form", row.form || "");
  return `task.html?${params.toString()}`;
}

function accuracyCaseHref(row) {
  const params = new URLSearchParams();
  params.set("candidate", row.candidate || "");
  params.set("entry", row.release_entry_id || "");
  params.set("form", row.form || "");
  return `accuracy-case.html?${params.toString()}`;
}

function yesNo(value) {
  return value ? t("yes") : t("no");
}

function appendDetailValue(parent, value) {
  if (Array.isArray(value)) {
    if (value.length === 0) {
      parent.textContent = "-";
      return;
    }
    parent.textContent = value.map((item) => text(item)).join(", ");
    return;
  }
  if (value instanceof Node) {
    parent.append(value);
    return;
  }
  parent.textContent = text(value);
}

function detailGroup(label, value) {
  const group = make("div");
  const dd = make("dd");
  group.append(make("dt", "", label), dd);
  appendDetailValue(dd, value);
  return group;
}

function renderDetailGroups(id, rows) {
  const container = byId(id);
  if (!container) {
    return;
  }
  container.replaceChildren(
    ...rows
      .filter(([, value]) => value !== undefined && value !== null && !(Array.isArray(value) && value.length === 0))
      .map(([label, value]) => detailGroup(label, value)),
  );
}

function sourceLink(path, label) {
  if (!path) {
    return make("span", "table-note", t("sourceUnavailable"));
  }
  const wrapper = make("div", "source-link");
  const anchor = make("a", "text-link", label);
  anchor.href = githubSourceHref(path);
  anchor.target = "_blank";
  anchor.rel = "noopener";
  wrapper.append(anchor, codeText(path));
  return wrapper;
}

function contentKindLabel(kind) {
  return {
    prompt: t("contentKindPrompt"),
    checks: t("contentKindChecks"),
    meta: t("contentKindMeta"),
    release_task: t("contentKindReleaseTask"),
    gold: t("contentKindGold"),
    reference_answer: t("contentKindReferenceAnswer"),
    reference_testbench: t("contentKindReferenceTestbench"),
    supplied_artifact: t("contentKindSuppliedArtifact"),
  }[kind] || text(kind);
}

function findTaskRow(entry, form) {
  const rows = state.payloads.tasks?.rows || [];
  return rows.find((row) => {
    const entryMatches = row.release_entry_id === entry || row.task_id === entry || row.legacy_task_id === entry;
    return entryMatches && (!form || row.form === form);
  });
}

function findTaskDetail(entry, form) {
  const rows = state.payloads.taskDetails?.rows || [];
  return rows.find((row) => row.release_entry_id === entry && (!form || row.form === form));
}

function findAlignmentRow(entry, form) {
  const rows = state.payloads.alignment?.rows || [];
  return rows.find((row) => row.release_entry_id === entry && (!form || row.form === form));
}

function taskMetricCasesFor(entry, form) {
  return (state.payloads.precision?.task_metric_rows || []).filter((row) => row.release_entry_id === entry && (!form || row.form === form));
}

function findAccuracyCase(candidate, entry, form) {
  return (state.payloads.precision?.task_metric_rows || []).find(
    (row) => row.candidate === candidate && row.release_entry_id === entry && (!form || row.form === form),
  );
}

function metricCard(label, value, detail) {
  const card = make("article", "metric-card");
  card.append(make("span", "", label), make("strong", "", value), make("p", "", detail));
  return card;
}

function connectedModelCount() {
  const names = new Set();
  VERIFIED_LEADERBOARD_ROWS.forEach((row) => {
    if (row.model) {
      names.add(row.model);
    }
  });
  SMOKE_ROWS.forEach((row) => {
    if (row.model) {
      names.add(row.model);
    }
  });
  return names.size;
}

function renderHomeScorePlot() {
  const container = byId("home-score-plot");
  if (!container) {
    return;
  }
  const axis = make("div", "score-axis");
  [0, 20, 40, 60, 80, 100].forEach((tick) => {
    axis.append(make("span", "", `${tick}%`));
  });
  const body = make("div", "score-plot-body");
  if (VERIFIED_LEADERBOARD_ROWS.length === 0) {
    body.append(make("strong", "", t("scorePlotPending")), make("p", "", t("scorePlotPendingBody")), pill("pending", t("notRanked")));
  }
  container.replaceChildren(make("span", "score-plot-label", t("scorePlotAxis")), axis, body);
}

function renderHomeLeaderboardPreview() {
  const preview = byId("home-leaderboard-preview");
  if (!preview) {
    return;
  }
  const panel = make("div", "leaderboard-card");
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const header = document.createElement("tr");
  [t("thModel"), t("thStatus"), t("thEVAS"), t("thSpectre")].forEach((label) => header.append(make("th", "", label)));
  thead.append(header);
  const tbody = document.createElement("tbody");
  if (VERIFIED_LEADERBOARD_ROWS.length > 0) {
    VERIFIED_LEADERBOARD_ROWS.slice(0, 5).forEach((row) => {
      const tr = document.createElement("tr");
      [
        [t("thModel"), row.model],
        ["Pass@1", percent(row.pass_rate)],
        [t("thSpectre"), row.judge || "Spectre"],
      ].forEach(([label, value]) => {
        const td = make("td", "", value);
        td.dataset.label = label;
        tr.append(td);
      });
      tbody.append(tr);
    });
  } else {
    SMOKE_ROWS.forEach((row) => {
      const tr = document.createElement("tr");
      const modelCell = make("td", "", row.model);
      modelCell.dataset.label = t("thModel");
      const statusCell = make("td", "", "");
      statusCell.dataset.label = t("thStatus");
      statusCell.append(pill(row.status, t("integrationSmokePassed")));
      const evasCell = make("td", "table-note", t("smokeEvasShort"));
      evasCell.dataset.label = t("thEVAS");
      const spectreCell = make("td", "", state.language === "zh" ? t("notRun") : row.spectre);
      spectreCell.dataset.label = t("thSpectre");
      tr.append(modelCell, statusCell, evasCell, spectreCell);
      tbody.append(tr);
    });
  }
  table.append(thead, tbody);
  const wrap = make("div", "table-wrap compact-table");
  wrap.append(table);
  panel.append(make("h3", "", t("smokeTestedModels")), wrap);
  preview.replaceChildren(panel);
}

function selectHomeTaskExamples(rows) {
  const picked = [];
  const seenCategories = new Set();
  const candidates = [...rows]
    .filter((row) => row.release_entry_id && row.form && row.certification === "certified")
    .sort((a, b) => {
      const scoreA = (a.counted_in_score ? 0 : 1) + (a.difficulty === "D3" ? -0.2 : 0);
      const scoreB = (b.counted_in_score ? 0 : 1) + (b.difficulty === "D3" ? -0.2 : 0);
      return scoreA - scoreB;
    });
  for (const row of candidates) {
    if (picked.length >= 6) {
      break;
    }
    if (seenCategories.has(row.category)) {
      continue;
    }
    picked.push(row);
    seenCategories.add(row.category);
  }
  for (const row of candidates) {
    if (picked.length >= 6) {
      break;
    }
    if (!picked.includes(row)) {
      picked.push(row);
    }
  }
  return picked;
}

function renderHomeTaskExamples() {
  const container = byId("home-task-examples");
  if (!container) {
    return;
  }
  const rows = state.payloads.tasks?.rows || [];
  const examples = selectHomeTaskExamples(rows);
  container.replaceChildren(
    ...examples.map((row) => {
      const anchor = make("a", "task-example-card");
      anchor.href = taskHref(row);
      const meta = make("div", "task-example-meta");
      meta.append(pill(row.level, row.level), pill(row.form, row.form), pill(row.difficulty, row.difficulty));
      anchor.append(
        make("span", "news-meta", categoryLabel(row.category)),
        make("strong", "", row.base_function || row.release_entry_id),
        make("p", "", `${row.release_entry_id}:${row.form}`),
        meta,
        make("span", "text-link table-link", t("taskExampleCta")),
      );
      return anchor;
    }),
  );
}

function option(value, label) {
  const element = document.createElement("option");
  element.value = value;
  element.textContent = label || value;
  return element;
}

function populateSelect(id, values, labeler = (value) => value) {
  const select = byId(id);
  if (!select) {
    return;
  }
  const selected = select.value;
  select.replaceChildren(option("", t("allOption")), ...values.map((value) => option(value, labeler(value))));
  if ([...select.options].some((item) => item.value === selected)) {
    select.value = selected;
  }
}

function uniqueValues(rows, key) {
  return [...new Set(rows.map((row) => row[key]).filter(Boolean))].sort();
}

function applyStaticTranslations() {
  document.documentElement.lang = state.language === "zh" ? "zh-Hans" : "en";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
  const toggle = byId("language-toggle");
  if (toggle) {
    toggle.setAttribute("aria-pressed", state.language === "zh" ? "true" : "false");
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url}: ${response.status}`);
  }
  return response.json();
}

function renderFooter() {
  const generated = state.payloads.summary?.generated_at || state.payloads.modelRoster?.date || "";
  const node = byId("generated-at");
  if (node) {
    node.textContent = generated ? `${generated}` : "";
  }
}

function renderNewsList(id, limit) {
  const container = byId(id);
  if (!container) {
    return;
  }
  const rows = limit ? NEWS_ITEMS.slice(0, limit) : NEWS_ITEMS;
  container.replaceChildren(
    ...rows.map((item) => {
      const anchor = document.createElement("a");
      anchor.className = "news-item";
      anchor.href = item.href;
      anchor.append(
        make("span", "news-meta", `${item.date} · ${item.type}`),
        make("strong", "", item.title[state.language]),
        make("p", "", item.body[state.language]),
      );
      return anchor;
    }),
  );
}

function renderHome() {
  const summary = state.payloads.summary?.summary || {};
  const model = state.payloads.modelRoster?.summary || {};
  const categories = state.payloads.categories?.rows || [];
  const metrics = byId("home-metrics");
  if (metrics) {
    metrics.replaceChildren(
      metricCard(t("metricBenchmarkRows"), number(summary.form_count), t("detailSingleDenominator")),
      metricCard(t("metricReleaseEntries"), number(summary.entry_count), t("detailFunctionEntries")),
      metricCard(t("metricCategories"), number(categories.length), t("detailFunctionFamilies")),
      metricCard(t("connectedModels"), number(connectedModelCount() || model.connected_model_count || 0), t("detailConnectedModels")),
    );
  }
  renderHomeScorePlot();
  renderHomeLeaderboardPreview();
  renderHomeTaskExamples();
  renderNewsList("home-news-list", 3);
}

function renderLeaderboard() {
  const tbody = byId("leaderboard-table");
  if (tbody) {
    if (VERIFIED_LEADERBOARD_ROWS.length === 0) {
      const tr = document.createElement("tr");
      const td = make("td", "", "");
      td.colSpan = 7;
      const empty = make("div", "empty-state");
      empty.append(pill("pending", t("noVerifiedRuns")), make("p", "", t("noVerifiedRunsDetail")));
      td.append(empty);
      tr.append(td);
      tbody.replaceChildren(tr);
    }
  }

  const smoke = byId("smoke-table");
  if (smoke) {
    smoke.replaceChildren(
      ...SMOKE_ROWS.map((row) => {
        const tr = document.createElement("tr");
        tr.append(
          make("td", "", row.model),
          make("td", "", ""),
          make("td", "table-note", state.language === "zh" ? t("generatedScoredFailed") : row.evas),
          make("td", "", state.language === "zh" ? t("notRun") : row.spectre),
        );
        tr.children[1].append(pill(row.status, t("integrationSmokePassed")));
        return tr;
      }),
    );
  }

  const commands = byId("leaderboard-commands");
  const examples = state.payloads.modelRoster?.example_commands || {};
  if (commands) {
    const items = [
      [t("listRoster"), examples.list_roster || "python3 runners/run_vabench_model_eval.py --list"],
      [t("evasOnlyBaseline"), examples.evas_only_baseline],
      [t("fullEvalWithSpectre"), examples.full_eval_with_spectre],
    ].filter(([, command]) => command);
    commands.replaceChildren(
      ...items.map(([label, command]) => {
        const group = make("div");
        group.append(make("dt", "", label), make("dd", "", command));
        return group;
      }),
    );
  }
}

function renderBenchmarkMetrics() {
  const summary = state.payloads.summary?.summary || {};
  const tasks = state.payloads.tasks?.summary || {};
  const model = state.payloads.modelRoster?.summary || {};
  const categories = state.payloads.categories?.rows || [];
  const metrics = byId("benchmark-metrics");
  if (!metrics) {
    return;
  }
  metrics.replaceChildren(
    metricCard(t("metricBenchmarkRows"), number(tasks.row_count || summary.form_count), t("detailSingleDenominator")),
    metricCard(t("metricReleaseEntries"), number(summary.entry_count), t("detailFunctionEntries")),
    metricCard(t("metricScoredRows"), number(model.scored_model_row_count || tasks.scored_rows), t("detailModelRoster")),
    metricCard(t("metricCategories"), number(categories.length), t("detailFunctionFamilies")),
  );
}

function renderCategories() {
  const tbody = byId("category-table");
  if (!tbody) {
    return;
  }
  tbody.replaceChildren(
    ...(state.payloads.categories?.rows || []).map((row) => {
      const tr = document.createElement("tr");
      tr.append(
        make("td", "", categoryLabel(row.category)),
        make("td", "", number(row.entry_count)),
        make("td", "", number(row.form_count)),
        make("td", "", number(row.l1_entry_count)),
        make("td", "", number(row.l2_entry_count)),
        make("td", "", number(row.scored_form_count)),
      );
      return tr;
    }),
  );
}

function initTaskFilters() {
  if (state.taskFiltersReady || !byId("task-search")) {
    return;
  }
  ["task-search", "filter-category", "filter-form", "filter-level", "filter-provenance"].forEach((id) => {
    byId(id)?.addEventListener("input", renderTaskTable);
  });
  byId("reset-filters")?.addEventListener("click", () => {
    ["task-search", "filter-category", "filter-form", "filter-level", "filter-provenance"].forEach((id) => {
      const node = byId(id);
      if (node) {
        node.value = "";
      }
    });
    renderTaskTable();
  });
  state.taskFiltersReady = true;
}

function setupTaskFilters() {
  const rows = state.tasks;
  populateSelect("filter-category", uniqueValues(rows, "category"), categoryLabel);
  populateSelect("filter-form", uniqueValues(rows, "form"));
  populateSelect("filter-level", uniqueValues(rows, "level"));
  populateSelect("filter-provenance", uniqueValues(rows, "provenance"), provenanceLabel);
  initTaskFilters();
}

function currentTaskRows() {
  const query = byId("task-search")?.value.trim().toLowerCase() || "";
  const category = byId("filter-category")?.value || "";
  const form = byId("filter-form")?.value || "";
  const level = byId("filter-level")?.value || "";
  const provenance = byId("filter-provenance")?.value || "";
  return state.tasks.filter((row) => {
    const localizedHaystack = [categoryLabel(row.category), provenanceLabel(row.provenance), policyLabel(row.parity_policy)]
      .join(" ")
      .toLowerCase();
    if (query && !String(row.search_text || "").includes(query) && !localizedHaystack.includes(query)) {
      return false;
    }
    return (!category || row.category === category) && (!form || row.form === form) && (!level || row.level === level) && (!provenance || row.provenance === provenance);
  });
}

function metricLine(row) {
  if (row.mean_relative_rms_error !== null && row.mean_relative_rms_error !== undefined) {
    return format("meanRmsLine", {
      mean: number(row.mean_relative_rms_error),
      worst: number(row.max_relative_rms_error),
    });
  }
  if (row.relative_gain_delta !== null && row.relative_gain_delta !== undefined) {
    return format("gainDeltaLine", { delta: number(row.relative_gain_delta) });
  }
  return policyLabel(row.parity_policy);
}

function renderTaskTable() {
  const rows = currentTaskRows();
  const count = byId("task-count");
  if (count) {
    count.textContent = format("rowsShown", { shown: number(rows.length), total: number(state.tasks.length) });
  }
  const tbody = byId("task-table");
  if (!tbody) {
    return;
  }
  if (rows.length === 0) {
    const tr = document.createElement("tr");
    const td = make("td", "", t("noRowsMatch"));
    td.colSpan = 7;
    tr.append(td);
    tbody.replaceChildren(tr);
    return;
  }
  tbody.replaceChildren(
    ...rows.map((row) => {
      const tr = document.createElement("tr");
      const task = make("td");
      const taskTitle = make("div", "task-title");
      const taskLink = make("a", "text-link table-link", text(row.base_function));
      taskLink.href = taskHref(row);
      taskTitle.append(taskLink, codeText(row.task_id), make("small", "", text(row.release_entry_id)));
      task.append(taskTitle);

      const category = make("td");
      category.append(
        make("strong", "", categoryLabel(row.category)),
        make("div", "table-note", `${text(row.difficulty)} · ${text(row.track)} · ${provenanceLabel(row.provenance)}`),
      );

      const backend = make("td");
      const backendStack = make("div", "backend-stack");
      backendStack.append(pill(row.static, t("staticBackend")), pill(row.evas, t("evasBackend")), pill(row.spectre, t("spectreBackend")));
      backend.append(backendStack);

      const parity = make("td");
      parity.append(pill(row.parity_status), make("div", "table-note", metricLine(row)));

      tr.append(
        task,
        category,
        make("td", "", text(row.form)),
        make("td", "", text(row.level)),
        make("td", "", row.counted_in_score ? t("counted") : t("notCounted")),
        backend,
        parity,
      );
      return tr;
    }),
  );
}

function renderBenchmark() {
  state.tasks = state.payloads.tasks?.rows || [];
  renderBenchmarkMetrics();
  renderCategories();
  setupTaskFilters();
  renderTaskTable();
}

function renderTaskDetailMissing() {
  const title = byId("task-detail-title");
  const intro = byId("task-detail-intro");
  if (title) {
    title.textContent = t("taskDetailMissing");
  }
  if (intro) {
    intro.textContent = t("taskDetailMissingBody");
  }
  const metrics = byId("task-detail-metrics");
  if (metrics) {
    metrics.replaceChildren(metricCard(t("thStatus"), t("taskDetailMissing"), t("taskDetailMissingBody")));
  }
  ["task-detail-identity", "task-detail-assets", "task-detail-evaluation", "task-detail-precision", "task-detail-content-list"].forEach((id) => {
    const node = byId(id);
    if (node) {
      node.replaceChildren();
    }
  });
  const tbody = byId("task-detail-accuracy-table");
  if (tbody) {
    tbody.replaceChildren();
  }
}

function renderTaskDetailAccuracyCases(cases) {
  const tbody = byId("task-detail-accuracy-table");
  if (!tbody) {
    return;
  }
  if (cases.length === 0) {
    const tr = document.createElement("tr");
    const td = make("td", "", t("taskDetailNoAccuracyCase"));
    td.colSpan = 5;
    tr.append(td);
    tbody.replaceChildren(tr);
    return;
  }
  tbody.replaceChildren(
    ...cases.map((row) => {
      const tr = document.createElement("tr");
      const caseLink = make("a", "text-link table-link", t("viewAccuracyCase"));
      caseLink.href = accuracyCaseHref(row);
      const diagnostic = make("td");
      diagnostic.append(pill(row.diagnostic_waveform_status), make("div", "table-note", text(row.diagnostic_note)));
      tr.append(
        make("td", "", text(row.candidate_label)),
        make("td", "", preciseNumber(row.relative_gain_delta)),
        diagnostic,
        make("td", "", preciseNumber(row.diagnostic_waveform_worst_signal_relative_rms_error)),
        make("td", "", ""),
      );
      tr.lastChild.append(caseLink);
      return tr;
    }),
  );
}

function fileBaseName(path) {
  const parts = String(path || "").split("/");
  return parts[parts.length - 1] || "";
}

function isBuggyArtifact(file) {
  return /(^|[_/-])buggy([_.-]|$)/i.test(fileBaseName(file.path));
}

function isSpectreTestbench(file) {
  const name = fileBaseName(file.path).toLowerCase();
  return name.endsWith(".scs") || name.startsWith("tb_");
}

function classifyCoreFile(file) {
  if (file.kind === "prompt") {
    return "prompt";
  }
  if (file.kind === "checks") {
    return "evaluation";
  }
  if (file.kind === "gold") {
    if (isBuggyArtifact(file)) {
      return "supplied";
    }
    if (isSpectreTestbench(file)) {
      return "testbench";
    }
    return "answer";
  }
  return "advanced";
}

function renderContentFile(file, index, options = {}) {
  const item = document.createElement("details");
  item.className = "content-file";
  item.open = options.open ?? (index === 0 || file.kind === "checks");

  const summary = document.createElement("summary");
  const title = make("span", "content-file-title");
  const kindLabel = contentKindLabel(options.kind || file.kind);
  const fileLabel = options.label || file.label || kindLabel;
  title.append(make("strong", "", fileLabel));
  if (fileLabel !== kindLabel) {
    title.append(make("span", "", kindLabel));
  }
  const meta = make("span", "content-file-meta");
  meta.append(
    make("span", "", format("fileBytes", { count: number(file.size_bytes) })),
    file.truncated ? pill("pending", t("fileTruncated")) : make("span", "", text(file.language)),
  );
  const source = make("a", "text-link", t("openSource"));
  source.href = githubSourceHref(file.path);
  source.target = "_blank";
  source.rel = "noopener";
  source.addEventListener("click", (event) => event.stopPropagation());
  summary.append(title, meta, source);

  const path = codeText(file.path);
  path.classList.add("content-path");
  const pre = document.createElement("pre");
  const code = document.createElement("code");
  code.textContent = file.exists ? file.content || "" : t("fileMissing");
  pre.append(code);
  item.append(summary, path, pre);
  return item;
}

function renderCoreFileGroup(titleKey, bodyKey, files, kind, defaultOpen = false) {
  const section = document.createElement("section");
  section.className = "content-core-group";
  const heading = make("div", "content-core-heading");
  heading.append(make("h3", "", t(titleKey)), make("p", "", t(bodyKey)));
  const list = make("div", "content-browser compact");
  list.append(...files.map((file, index) => renderContentFile(file, index, { kind, open: defaultOpen || index === 0 })));
  section.append(heading, list);
  return section;
}

function renderTaskDetailContents(row) {
  const container = byId("task-detail-content-list");
  if (!container) {
    return;
  }
  const detail = findTaskDetail(row.release_entry_id, row.form);
  const files = (detail?.files || []).filter((file) => file && file.path);
  if (files.length === 0) {
    const empty = make("div", "empty-state");
    empty.append(make("p", "", t("taskDetailNoContents")));
    container.replaceChildren(empty);
    return;
  }
  const groups = {
    prompt: [],
    answer: [],
    testbench: [],
    evaluation: [],
    supplied: [],
    advanced: [],
  };
  files.forEach((file) => groups[classifyCoreFile(file)].push(file));

  const core = make("div", "content-core");
  [
    ["taskDetailCorePromptTitle", "taskDetailCorePromptBody", groups.prompt, "prompt", true],
    ["taskDetailCoreAnswerTitle", "taskDetailCoreAnswerBody", groups.answer, "reference_answer", true],
    ["taskDetailCoreTestbenchTitle", "taskDetailCoreTestbenchBody", groups.testbench, "reference_testbench", true],
    ["taskDetailCoreEvaluationTitle", "taskDetailCoreEvaluationBody", groups.evaluation, "checks", true],
    ["taskDetailCoreSuppliedTitle", "taskDetailCoreSuppliedBody", groups.supplied, "supplied_artifact", false],
  ].forEach(([titleKey, bodyKey, groupFiles, kind, defaultOpen]) => {
    if (groupFiles.length) {
      core.append(renderCoreFileGroup(titleKey, bodyKey, groupFiles, kind, defaultOpen));
    }
  });

  const advanced = document.createElement("details");
  advanced.className = "content-advanced";
  const summary = document.createElement("summary");
  summary.append(make("strong", "", t("taskDetailAdvancedTitle")), make("span", "", t("taskDetailAdvancedDescription")));
  advanced.append(summary);
  const advancedList = make("div", "content-browser compact");
  advancedList.append(...files.map((file, index) => renderContentFile(file, index, { open: false })));
  advanced.append(advancedList);

  container.replaceChildren(core, advanced);
}

function renderTaskDetail() {
  const entry = queryParam("id") || queryParam("entry");
  const form = queryParam("form");
  const row = findTaskRow(entry, form);
  if (!row) {
    renderTaskDetailMissing();
    return;
  }
  const alignment = findAlignmentRow(row.release_entry_id, row.form) || {};
  const cases = taskMetricCasesFor(row.release_entry_id, row.form);
  const title = byId("task-detail-title");
  const intro = byId("task-detail-intro");
  if (title) {
    title.textContent = `${text(row.release_entry_id)}:${text(row.form)}`;
  }
  if (intro) {
    intro.textContent = `${text(row.base_function)} · ${categoryLabel(row.category)} · ${text(row.level)} · ${text(row.difficulty)}`;
  }
  const metrics = byId("task-detail-metrics");
  if (metrics) {
    metrics.replaceChildren(
      metricCard(t("labelVerdict"), statusLabel(row.verdict), `${t("labelStatic")} ${statusLabel(row.static)} · ${t("labelEvas")} ${statusLabel(row.evas)} · ${t("labelSpectre")} ${statusLabel(row.spectre)}`),
      metricCard(t("labelScoreSurface"), yesNo(row.counted_in_score), row.counted_in_score ? t("counted") : t("notCounted")),
      metricCard(t("labelParityStatus"), statusLabel(row.parity_status), policyLabel(row.parity_policy)),
      metricCard(t("taskDetailAccuracyCasesTitle"), number(cases.length), t("taskMetricDescription")),
    );
  }
  renderDetailGroups("task-detail-identity", [
    [t("labelReleaseEntry"), row.release_entry_id],
    [t("labelTaskId"), row.task_id],
    [t("labelLegacyTaskId"), row.legacy_task_id],
    [t("labelIdNamespace"), idNamespaceMeaning(row.release_entry_id)],
    [t("labelBaseFunction"), row.base_function],
    [t("labelCategory"), categoryLabel(row.category)],
    [t("labelForm"), row.form],
    [t("labelLevel"), row.level],
    [t("labelDifficulty"), row.difficulty],
    [t("labelTrack"), row.track],
    [t("labelFamily"), row.family],
    [t("labelProvenance"), provenanceLabel(row.provenance)],
    [t("labelScoreSurface"), yesNo(row.counted_in_score)],
    [t("labelContentDenominator"), yesNo(row.content_denominator_included)],
  ]);
  renderDetailGroups("task-detail-assets", [
    [t("labelPromptPath"), sourceLink(row.prompt, t("openPrompt"))],
    [t("labelChecksPath"), sourceLink(row.checks, t("openChecks"))],
    [t("labelMetaPath"), sourceLink(row.meta, t("openMeta"))],
    [t("labelReleaseManifestPath"), sourceLink(row.release_task_manifest, t("openReleaseManifest"))],
    [t("labelEvidencePath"), sourceLink(row.evidence, t("openEvidence"))],
    [t("labelGoldCount"), number(row.gold_count)],
  ]);
  renderDetailGroups("task-detail-evaluation", [
    [t("labelStatic"), pill(row.static)],
    [t("labelEvas"), pill(row.evas)],
    [t("labelSpectre"), pill(row.spectre)],
    [t("labelVerdict"), pill(row.verdict)],
    [t("labelParityStatus"), pill(row.parity_status)],
    [t("labelParityPolicy"), policyLabel(row.parity_policy)],
    [t("labelSourceEquivalence"), yesNo(row.source_equivalence_pass)],
    [t("labelAlignmentStatus"), alignment.alignment_status ? pill(alignment.alignment_status) : undefined],
    [t("labelEqualityClaim"), translated(alignment.equality_claim)],
  ]);
  renderDetailGroups("task-detail-precision", [
    [t("labelMetricFamily"), translated(alignment.metric_family)],
    [t("labelSimilarity"), translated(alignment.similarity_summary)],
    [t("labelTolerance"), `${translated(alignment.tolerance_profile)}; ${translated(alignment.tolerance_result)}`],
    [t("labelWaveformStatus"), alignment.waveform_comparison_status ? pill(alignment.waveform_comparison_status) : undefined],
    [t("labelSignalsCompared"), number(row.signals_compared ?? alignment.signals_compared)],
    [t("labelSamples"), number(row.samples ?? alignment.samples)],
    [t("labelMeanRms"), preciseNumber(row.mean_relative_rms_error ?? alignment.mean_relative_rms_error)],
    [t("labelWorstRms"), preciseNumber(row.max_relative_rms_error ?? alignment.max_relative_rms_error)],
    [t("labelMaxRmse"), preciseNumber(row.max_rmse_v ?? alignment.max_rmse_v)],
    [t("labelMaxAbs"), preciseNumber(row.max_abs_v ?? alignment.max_abs_v)],
    [t("labelDigitalMismatch"), preciseNumber(row.max_digital_mismatch_ratio ?? alignment.max_digital_mismatch_ratio)],
    [t("labelRelativeGainDelta"), preciseNumber(row.relative_gain_delta ?? alignment.relative_gain_delta)],
  ]);
  renderTaskDetailContents(row);
  renderTaskDetailAccuracyCases(cases);
}

function renderProtocolMetrics() {
  const alignment = state.payloads.alignment?.summary || {};
  const summary = state.payloads.summary?.summary || {};
  const backends = state.payloads.backends || {};
  const metrics = byId("protocol-metrics");
  if (!metrics) {
    return;
  }
  metrics.replaceChildren(
    metricCard(t("metricAlignedRows"), number(alignment.aligned_row_count), t("detailSpectreAligned")),
    metricCard(t("metricBitExact"), translated(alignment.bit_exact_claim), t("detailNotAsserted")),
    metricCard(t("metricBackendCertified"), `${number(backends.certified_backend_count)} / ${number(backends.required_backend_count)}`, t("detailCertifiedSurfaces")),
    metricCard(t("metricMismatch"), number(summary.evas_pass_spectre_fail_count), t("detailAuditedMismatch")),
  );
}

function renderBackends() {
  const tbody = byId("backend-table");
  if (!tbody) {
    return;
  }
  const rows = [...(state.payloads.backends?.rows || [])].sort((a, b) => (b.pass_rate || 0) - (a.pass_rate || 0));
  tbody.replaceChildren(
    ...rows.map((row) => {
      const tr = document.createElement("tr");
      const backend = make("td");
      const stack = make("div", "task-title");
      stack.append(make("strong", "", translated(row.label)), make("small", "", text(row.backend)));
      backend.append(stack);

      const behavior = make("td");
      const behaviorStack = make("div", "parity-stack");
      behaviorStack.append(
        pill(row.certification_passed, row.certification_passed ? t("certified") : t("notCertified")),
        make("span", "table-note", format("rowsWithRate", { passed: number(row.pass_rows), total: number(row.total_rows), rate: percent(row.pass_rate) })),
        rateBar(row.pass_rate),
      );
      if (row.behavior_checker_missing_rows !== null && row.behavior_checker_missing_rows !== undefined) {
        behaviorStack.append(make("span", "table-note", format("missingCheckers", { count: number(row.behavior_checker_missing_rows) })));
      }
      behavior.append(behaviorStack);

      const evidence = make("td");
      evidence.append(codeText(row.evidence), make("div", "table-note", translated(row.notes)));

      const status = make("td");
      status.append(pill(row.status));
      tr.append(backend, status, make("td", "", `${number(row.pass_rows)} / ${number(row.total_rows)}`), behavior, evidence);
      return tr;
    }),
  );
}

function renderClaimBoundary() {
  const list = byId("protocol-list");
  if (list) {
    const boundary = state.payloads.summary?.claim_boundary || [];
    list.replaceChildren(
      ...boundary.map((item) => {
        const li = make("li", "", translated(item));
        return li;
      }),
    );
  }
  const terms = byId("parity-terms");
  if (terms) {
    const contract = state.payloads.summary?.equivalence_contract || {};
    const labels = {
      acceptance_basis: t("acceptanceBasis"),
      bit_exact_claim: t("bitExactEquality"),
      relative_rms_gate: t("relativeRmsGate"),
      small_absolute_gate: t("smallAbsoluteGate"),
      gain_metric_gate: t("gainMetricGate"),
      pll_task_aware: t("pllRows"),
      edge_window_policy: t("edgeWindowPolicy"),
    };
    terms.replaceChildren(
      ...Object.entries(labels)
        .filter(([key]) => contract[key] !== undefined)
        .map(([key, label]) => {
          const group = make("div");
          group.append(make("dt", "", label), make("dd", "", translated(contract[key])));
          return group;
        }),
    );
  }
}

function initAlignmentFilters() {
  if (state.alignmentFiltersReady || !byId("alignment-search")) {
    return;
  }
  ["alignment-search", "filter-alignment-status", "filter-alignment-policy"].forEach((id) => {
    byId(id)?.addEventListener("input", renderAlignmentTable);
  });
  byId("reset-alignment-filters")?.addEventListener("click", () => {
    ["alignment-search", "filter-alignment-status", "filter-alignment-policy"].forEach((id) => {
      const node = byId(id);
      if (node) {
        node.value = "";
      }
    });
    renderAlignmentTable();
  });
  state.alignmentFiltersReady = true;
}

function setupAlignmentFilters() {
  const rows = state.alignment;
  populateSelect("filter-alignment-status", uniqueValues(rows, "alignment_status"), statusLabel);
  populateSelect("filter-alignment-policy", uniqueValues(rows, "parity_policy"), policyLabel);
  initAlignmentFilters();
}

function currentAlignmentRows() {
  const query = byId("alignment-search")?.value.trim().toLowerCase() || "";
  const status = byId("filter-alignment-status")?.value || "";
  const policy = byId("filter-alignment-policy")?.value || "";
  return state.alignment.filter((row) => {
    const haystack = [
      row.task_id,
      row.legacy_task_id,
      row.release_entry_id,
      row.category,
      categoryLabel(row.category),
      row.form,
      provenanceLabel(row.provenance),
      row.parity_policy,
      policyLabel(row.parity_policy),
      row.alignment_status,
      statusLabel(row.alignment_status),
      row.equality_claim,
      translated(row.equality_claim),
      row.metric_family,
      translated(row.metric_family),
      row.equivalence_basis,
      translated(row.equivalence_basis),
      row.similarity_summary,
      row.tolerance_profile,
      row.tolerance_result,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return (!query || haystack.includes(query)) && (!status || row.alignment_status === status) && (!policy || row.parity_policy === policy);
  });
}

function renderAlignmentTable() {
  const rows = currentAlignmentRows();
  const count = byId("alignment-count");
  if (count) {
    count.textContent = format("alignmentRowsShown", { shown: number(rows.length), total: number(state.alignment.length) });
  }
  const tbody = byId("alignment-table");
  if (!tbody) {
    return;
  }
  if (rows.length === 0) {
    const tr = document.createElement("tr");
    const td = make("td", "", t("noRowsMatch"));
    td.colSpan = 5;
    tr.append(td);
    tbody.replaceChildren(tr);
    return;
  }
  tbody.replaceChildren(
    ...rows.map((row) => {
      const tr = document.createElement("tr");
      const task = make("td");
      const taskTitle = make("div", "task-title");
      taskTitle.append(
        make("strong", "", text(row.task_id)),
        make("small", "", `${categoryLabel(row.category)} · ${text(row.form)} · ${provenanceLabel(row.provenance)} · ${translated(row.metric_family)}`),
      );
      task.append(taskTitle);

      const claim = make("td");
      const claimStack = make("div", "parity-stack");
      claimStack.append(pill(row.alignment_status), make("span", "table-note", translated(row.equality_claim)));
      claim.append(claimStack);

      const backends = make("td");
      const backendStack = make("div", "backend-stack");
      backendStack.append(
        pill(row.spectre_reference_status, t("spectreRef")),
        pill(row.spectre_ax_status, t("spectreAx")),
        pill(row.evas_rust_behavior_checker_pass, t("evasRust")),
        pill(row.evas_python_behavior_checker_pass, t("evasPython")),
      );
      backends.append(backendStack);

      tr.append(
        task,
        claim,
        backends,
        make("td", "table-note", `${translated(row.similarity_summary)}; ${translated(row.equivalence_basis)}`),
        make("td", "table-note", `${translated(row.tolerance_profile)}; ${translated(row.tolerance_result)}`),
      );
      return tr;
    }),
  );
}

function renderProtocol() {
  state.alignment = state.payloads.alignment?.rows || [];
  renderProtocolMetrics();
  renderBackends();
  renderClaimBoundary();
  setupAlignmentFilters();
  renderAlignmentTable();
}

function gateLabel(gate) {
  if (state.language === "zh") {
    return GATE_LABELS_ZH[gate.name] || gate.label || gate.name;
  }
  return gate.label || gate.name;
}

function gateMeaning(gate) {
  if (state.language === "zh") {
    return GATE_MEANINGS_ZH[gate.name] || gate.meaning || "";
  }
  return gate.meaning || "";
}

function taxonomyField(item, field) {
  if (state.language === "zh") {
    return TAXONOMY_ZH[item.name]?.[field] || item[field] || "";
  }
  return item[field] || "";
}

function explanationCard(titleKey, bodyKey, statusValue) {
  const card = make("article", "explanation-card");
  card.append(pill(statusValue, t(titleKey)), make("p", "", t(bodyKey)));
  return card;
}

function renderAccuracyMetrics() {
  const precision = state.payloads.precision || {};
  const summary = precision.summary || {};
  const metrics = byId("accuracy-metrics");
  if (!metrics) {
    return;
  }
  metrics.replaceChildren(
    metricCard(t("metricBenchmarkRows"), number(summary.benchmark_management_rows), t("detailCommonRows")),
    metricCard(t("metricFourwayRows"), number(summary.precision_evidence_rows || summary.fourway_common_rows), t("detailPrecisionRows")),
    metricCard(t("metricPrecisionComparisons"), ratioText(summary.precision_pass_comparisons, summary.precision_total_comparisons), t("detailPrecisionComparisons")),
    metricCard(t("metricTaskMetricRows"), number(summary.task_metric_comparisons), t("detailTaskMetricRows")),
  );
}

function renderAccuracyAnswer() {
  const container = byId("accuracy-answer");
  if (!container) {
    return;
  }
  container.replaceChildren(
    explanationCard("identicalNoTitle", "identicalNoBody", "not_asserted"),
    explanationCard("equivalentYesTitle", "equivalentYesBody", "equivalent_to_spectre_strict"),
    explanationCard("differenceTitle", "differenceBody", "pending"),
    explanationCard("toleranceAnchorTitle", "toleranceAnchorBody", "pass"),
  );
}

function renderAccuracyGates() {
  const terms = byId("accuracy-gates");
  if (!terms) {
    return;
  }
  const gates = state.payloads.precision?.gates || [];
  terms.replaceChildren(
    ...gates.map((gate) => {
      const group = make("div");
      const threshold = gate.threshold ? `${gate.threshold}. ` : "";
      group.append(make("dt", "", gateLabel(gate)), make("dd", "", `${threshold}${gateMeaning(gate)}`));
      return group;
    }),
  );
}

function renderPrecisionTable() {
  const tbody = byId("precision-table");
  if (!tbody) {
    return;
  }
  const rows = state.payloads.precision?.simulator_precision_rows || [];
  tbody.replaceChildren(
    ...rows.map((row) => {
      const tr = document.createElement("tr");
      const surface = make("td");
      const stack = make("div", "task-title");
      stack.append(make("strong", "", text(row.candidate_label)), make("small", "", `${text(row.candidate)} vs ${text(row.reference_label)}`));
      surface.append(stack);

      const equivalent = make("td");
      equivalent.append(
        pill(row.claim),
        make("div", "table-note", ratioText(row.equivalent_rows, row.compared_rows)),
        rateBar(row.equivalence_rate),
      );

      tr.append(
        surface,
        equivalent,
        make("td", "", `${number(row.task_metric_rows)} (${preciseNumber(row.max_task_metric_relative_delta)})`),
        make("td", "", preciseNumber(row.worst_effective_mean_relative_rms_error)),
        make("td", "", preciseNumber(row.worst_effective_signal_relative_rms_error)),
        make("td", "", preciseNumber(row.worst_raw_mean_relative_rms_error)),
        make("td", "", preciseNumber(row.worst_raw_signal_relative_rms_error)),
      );
      return tr;
    }),
  );
}

function renderTaskMetricRows() {
  const tbody = byId("task-metric-table");
  if (!tbody) {
    return;
  }
  const rows = state.payloads.precision?.task_metric_rows || [];
  tbody.replaceChildren(
    ...rows.map((row) => {
      const tr = document.createElement("tr");
      const task = make("td");
      const stack = make("div", "task-title");
      const rowLink = make("a", "text-link table-link", `${text(row.release_entry_id)}:${text(row.form)}`);
      rowLink.href = accuracyCaseHref(row);
      stack.append(
        rowLink,
        make("small", "", categoryLabel(row.category)),
      );
      task.append(stack);
      const diagnostic = make("td");
      diagnostic.append(pill(row.diagnostic_waveform_status), make("div", "table-note", text(row.diagnostic_note)));
      tr.append(
        make("td", "", text(row.candidate_label)),
        task,
        make("td", "", translated(row.acceptance_policy)),
        make("td", "", preciseNumber(row.relative_gain_delta)),
        diagnostic,
        make("td", "", preciseNumber(row.diagnostic_waveform_mean_relative_rms_error)),
        make("td", "", preciseNumber(row.diagnostic_waveform_worst_signal_relative_rms_error)),
      );
      return tr;
    }),
  );
}

function renderPointwiseTaxonomy() {
  const container = byId("pointwise-taxonomy");
  if (!container) {
    return;
  }
  const rows = state.payloads.precision?.pointwise_difference_taxonomy || [];
  const detailFields = [
    ["taxonomySymptom", "what_changes"],
    ["taxonomyShortcoming", "known_shortcoming"],
    ["taxonomyHandling", "current_handling"],
    ["taxonomyBugSignal", "bug_signal"],
    ["taxonomyFeedback", "feedback_wanted"],
    ["taxonomyRule", "reporting_rule"],
  ];
  container.replaceChildren(
    ...rows.map((item) => {
      const card = make("article", "taxonomy-card");
      const details = make("dl", "taxonomy-detail");
      detailFields.forEach(([labelKey, field]) => {
        const value = taxonomyField(item, field);
        if (value) {
          details.append(make("dt", "", t(labelKey)), make("dd", "", value));
        }
      });
      card.append(
        make("span", "", taxonomyField(item, "label")),
        make("strong", "", taxonomyField(item, "why_expected")),
        details,
      );
      return card;
    }),
  );
}

function renderSpectreAnchor() {
  const tbody = byId("spectre-anchor-table");
  if (!tbody) {
    return;
  }
  const anchor = state.payloads.precision?.spectre_self_consistency || {};
  const rows = [
    [t("anchorComparedPairs"), number(anchor.compared_pairs)],
    [t("anchorPassedPairs"), number(anchor.passed_pairs)],
    [t("anchorNeedsReviewPairs"), number(anchor.needs_review_pairs)],
    [t("anchorRowMeanMax"), preciseNumber(anchor.row_mean_relative_rms_max)],
    [t("anchorWorstSignalMax"), preciseNumber(anchor.worst_signal_relative_rms_max)],
    [t("anchorMaxPointAbs"), `${preciseNumber(anchor.max_point_abs_v)} V`],
  ];
  tbody.replaceChildren(
    ...rows.map(([label, value]) => {
      const tr = document.createElement("tr");
      tr.append(make("td", "", label), make("td", "", value));
      return tr;
    }),
  );
}

function renderAccuracyCaseMissing() {
  const title = byId("accuracy-case-title");
  const intro = byId("accuracy-case-intro");
  if (title) {
    title.textContent = t("accuracyCaseMissing");
  }
  if (intro) {
    intro.textContent = t("accuracyCaseMissingBody");
  }
  const metrics = byId("accuracy-case-metrics");
  if (metrics) {
    metrics.replaceChildren(metricCard(t("thStatus"), t("accuracyCaseMissing"), t("accuracyCaseMissingBody")));
  }
  ["accuracy-case-detail", "accuracy-case-task", "accuracy-case-taxonomy"].forEach((id) => {
    const node = byId(id);
    if (node) {
      node.replaceChildren();
    }
  });
}

function caseTaxonomyRows(row) {
  const taxonomy = state.payloads.precision?.pointwise_difference_taxonomy || [];
  const names = ["task_metric_gate", "noise_like_or_dithered_stimulus", "solver_sampling_grid", "interpolation"];
  if (row.diagnostic_waveform_status === "needs_review") {
    names.push("edge_window", "event_time_and_cross");
  }
  return names.map((name) => taxonomy.find((item) => item.name === name)).filter(Boolean);
}

function renderAccuracyCaseTaxonomy(row) {
  const container = byId("accuracy-case-taxonomy");
  if (!container) {
    return;
  }
  const detailFields = [
    ["taxonomyShortcoming", "known_shortcoming"],
    ["taxonomyHandling", "current_handling"],
    ["taxonomyBugSignal", "bug_signal"],
    ["taxonomyFeedback", "feedback_wanted"],
  ];
  container.replaceChildren(
    ...caseTaxonomyRows(row).map((item) => {
      const card = make("article", "taxonomy-card");
      const details = make("dl", "taxonomy-detail");
      detailFields.forEach(([labelKey, field]) => {
        const value = taxonomyField(item, field);
        if (value) {
          details.append(make("dt", "", t(labelKey)), make("dd", "", value));
        }
      });
      card.append(make("span", "", taxonomyField(item, "label")), make("strong", "", taxonomyField(item, "why_expected")), details);
      return card;
    }),
  );
}

function renderAccuracyCase() {
  const candidate = queryParam("candidate");
  const entry = queryParam("entry") || queryParam("id");
  const form = queryParam("form");
  const row = findAccuracyCase(candidate, entry, form);
  if (!row) {
    renderAccuracyCaseMissing();
    return;
  }
  const task = findTaskRow(row.release_entry_id, row.form) || {};
  const title = byId("accuracy-case-title");
  const intro = byId("accuracy-case-intro");
  if (title) {
    title.textContent = `${text(row.candidate_label)} · ${text(row.release_entry_id)}:${text(row.form)}`;
  }
  if (intro) {
    intro.textContent = `${categoryLabel(row.category)} · ${translated(row.acceptance_policy)}`;
  }
  const metrics = byId("accuracy-case-metrics");
  if (metrics) {
    metrics.replaceChildren(
      metricCard(t("labelRelativeGainDelta"), preciseNumber(row.relative_gain_delta), translated(row.acceptance_policy)),
      metricCard(t("labelWaveformStatus"), statusLabel(row.diagnostic_waveform_status), text(row.diagnostic_note)),
      metricCard(t("labelMeanRms"), preciseNumber(row.diagnostic_waveform_mean_relative_rms_error), t("thDiagnosticMeanRms")),
      metricCard(t("labelWorstRms"), preciseNumber(row.diagnostic_waveform_worst_signal_relative_rms_error), t("thDiagnosticWorstSignalRms")),
    );
  }
  renderDetailGroups("accuracy-case-detail", [
    [t("labelCandidate"), row.candidate_label],
    [t("labelReleaseEntry"), row.release_entry_id],
    [t("labelForm"), row.form],
    [t("labelTaskId"), row.task_id],
    [t("labelLegacyTaskId"), row.legacy_task_id],
    [t("labelCategory"), categoryLabel(row.category)],
    [t("thAcceptancePolicy"), translated(row.acceptance_policy)],
    [t("labelRelativeGainDelta"), preciseNumber(row.relative_gain_delta)],
    [t("labelCandidateGain"), preciseNumber(row.candidate_gain)],
    [t("labelReferenceGain"), preciseNumber(row.reference_gain)],
    [t("labelWaveformStatus"), pill(row.diagnostic_waveform_status)],
    [t("labelDiagnosticNote"), row.diagnostic_note],
  ]);
  const taskLink = task.release_entry_id ? make("a", "text-link", t("accuracyCaseTaskLink")) : undefined;
  if (taskLink) {
    taskLink.href = taskHref(task);
  }
  renderDetailGroups("accuracy-case-task", [
    [t("labelBaseFunction"), task.base_function],
    [t("labelCategory"), task.category ? categoryLabel(task.category) : undefined],
    [t("labelLevel"), task.level],
    [t("labelDifficulty"), task.difficulty],
    [t("labelTrack"), task.track],
    [t("labelScoreSurface"), task.release_entry_id ? yesNo(task.counted_in_score) : undefined],
    [t("labelParityStatus"), task.parity_status ? pill(task.parity_status) : undefined],
    [t("accuracyCaseTaskLink"), taskLink],
  ]);
  renderAccuracyCaseTaxonomy(row);
}

function renderAccuracy() {
  renderAccuracyMetrics();
  renderAccuracyAnswer();
  renderAccuracyGates();
  renderPrecisionTable();
  renderTaskMetricRows();
  renderPointwiseTaxonomy();
  renderSpectreAnchor();
}

function renderNews() {
  renderNewsList("news-list");
}

function renderAll() {
  renderFooter();
  const page = document.body.dataset.page || "home";
  if (page === "home") {
    renderHome();
  } else if (page === "leaderboard") {
    renderLeaderboard();
  } else if (page === "benchmark") {
    renderBenchmark();
  } else if (page === "task-detail") {
    renderTaskDetail();
  } else if (page === "protocol") {
    renderProtocol();
  } else if (page === "accuracy") {
    renderAccuracy();
  } else if (page === "accuracy-case") {
    renderAccuracyCase();
  } else if (page === "news") {
    renderNews();
  }
}

function showError(error) {
  const main = document.querySelector("main");
  if (!main) {
    return;
  }
  const message = make("div", "load-error", format("loadError", { message: error.message }));
  main.prepend(message);
}

function initLanguageToggle() {
  const toggle = byId("language-toggle");
  if (!toggle) {
    return;
  }
  toggle.addEventListener("click", () => {
    state.language = state.language === "zh" ? "en" : "zh";
    localStorage.setItem(LANGUAGE_KEY, state.language);
    applyStaticTranslations();
    renderAll();
  });
}

async function boot() {
  initLanguageToggle();
  applyStaticTranslations();
  try {
    const page = document.body.dataset.page || "home";
    const [summary, backends, alignment, tasks, categories, modelRoster, precision, taskDetails] = await Promise.all([
      fetchJson(DATA.summary),
      fetchJson(DATA.backends),
      fetchJson(DATA.alignment),
      fetchJson(DATA.tasks),
      fetchJson(DATA.categories),
      fetchJson(DATA.modelRoster),
      fetchJson(DATA.precision),
      page === "task-detail" ? fetchJson(DATA.taskDetails) : Promise.resolve({ rows: [] }),
    ]);
    state.payloads = { summary, backends, alignment, tasks, categories, modelRoster, precision, taskDetails };
    renderAll();
  } catch (error) {
    showError(error);
    console.error(error);
  }
}

boot();
