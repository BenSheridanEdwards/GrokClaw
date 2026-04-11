# Graph Report - .  (2026-04-11)

## Corpus Check
- 721 files · ~648,599 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2945 nodes · 5056 edges · 309 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `execute()` - 51 edges
2. `WorkflowHealthTests` - 30 edges
3. `audit()` - 21 edges
4. `asString()` - 19 edges
5. `asRecord()` - 18 edges
6. `WorkflowHealthAuditDirectTests` - 18 edges
7. `_load_audit_module()` - 17 edges
8. `CronRunRecordTests` - 15 edges
9. `PolymarketTradeTests` - 15 edges
10. `asString()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `buildProcessConfig()` --calls--> `parseCommaArgs()`  [EXTRACTED]
  paperclip/ui/src/adapters/process/build-config.ts → paperclip/packages/adapters/codex-local/src/ui/build-config.ts
- `testEnvironment()` --calls--> `normalizeMethod()`  [EXTRACTED]
  paperclip/packages/adapters/pi-local/src/server/test.ts → paperclip/server/src/adapters/http/test.ts
- `testEnvironment()` --calls--> `isNonEmpty()`  [EXTRACTED]
  paperclip/packages/adapters/pi-local/src/server/test.ts → paperclip/packages/adapters/codex-local/src/server/test.ts
- `testEnvironment()` --calls--> `commandLooksLike()`  [EXTRACTED]
  paperclip/packages/adapters/pi-local/src/server/test.ts → paperclip/packages/adapters/codex-local/src/server/test.ts
- `testEnvironment()` --calls--> `isLoopbackHost()`  [EXTRACTED]
  paperclip/packages/adapters/pi-local/src/server/test.ts → paperclip/packages/adapters/openclaw-gateway/src/server/test.ts

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (109): formatVerb(), humanizeValue(), defaultSecretName(), emit(), removeRow(), sealRow(), updateRow(), AgentDetail() (+101 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (51): buildClaudeLocalConfig(), buildCodexLocalConfig(), buildCursorLocalConfig(), buildGeminiLocalConfig(), buildOpenClawGatewayConfig(), buildOpenCodeLocalConfig(), buildPiLocalConfig(), buildProcessConfig() (+43 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (76): appendWakeText(), asRecord(), autoApproveDevicePairing(), base64UrlEncode(), buildClaudeRuntimeConfig(), buildLoginResult(), buildPaperclipEnvForWake(), buildSessionPath() (+68 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (27): assigneeValueFromSelection(), currentUserAssigneeOption(), clearDraft(), handleSubmit(), parseReassignment(), applyMention(), hexToRgb(), mentionChipStyle() (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (33): serializeParams(), serializeRenderEnvironment(), serializeRenderEnvironmentSnapshot(), useHostContext(), usePluginAction(), usePluginBridgeContext(), usePluginData(), usePluginStream() (+25 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (30): defaultPathForPlatform(), ensureCommandResolvable(), ensurePathInEnv(), isMaintainerOnlySkillTarget(), listPaperclipSkillEntries(), normalizePathSlashes(), pathExists(), quoteForCmd() (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (6): ApiRequestError, buildUrl(), PaperclipApiClient, safeParseJson(), toApiError(), toStringRecord()

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (30): async(), cancelDraft(), getFoldedDocumentsStorageKey(), handleDraftBlur(), handleDraftKeyDown(), loadFoldedDocumentKeys(), saveFoldedDocumentKeys(), extractMermaidSource() (+22 more)

### Community 8 - "Community 8"
Cohesion: 0.1
Nodes (48): add_failure(), audit(), audit(), _grace_for_schedule(), audit_job(), JobExpectation, _last_expected_fire(), _load_cron_jobs() (+40 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (29): buildInviteOnboardingManifest(), buildInviteOnboardingTextDocument(), buildJoinDefaultsPayloadForAccept(), buildOnboardingConnectionCandidates(), buildOnboardingDiscoveryDiagnostics(), extractHeaderEntries(), extractInviteMessage(), generateEd25519PrivateKeyPem() (+21 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (33): ApiError, applyPendingMigrations(), applyPendingMigrationsManually(), columnExists(), constraintExists(), createUtilitySql(), discoverMigrationTableSchema(), ensureMigrationJournalTable() (+25 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (33): aggregate_top_trader_positions(), build_copy_signal(), build_signal_from_aggregate(), clear_staged_candidate(), fetch_bonding_traders(), fetch_json(), fetch_markets(), fetch_markets_page() (+25 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (32): branchExistsOnAnyRemote(), branchHasUniqueCommits(), copyDirectoryContents(), copyGitHooksToWorktreeGitDir(), copySeededSecretsKey(), detectGitBranchName(), detectGitWorkspaceInfo(), ensureEmbeddedPostgres() (+24 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (29): allocatePort(), buildTemplateData(), buildWorkspaceCommandEnv(), clearIdleTimer(), directoryExists(), ensureRuntimeServicesForRun(), isAbsolutePath(), normalizeAdapterManagedRuntimeServices() (+21 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (3): Git checkout preserves old mtimes; audit keys off cron record + prompt filename., Hourly line may use Alpha · Hourly · / Alpha (hourly): and leading whitespace., WorkflowHealthTests

### Community 15 - "Community 15"
Cohesion: 0.23
Nodes (28): asNumber(), asRecord(), asString(), collectTextEntries(), compactShellToolInput(), errorText(), extractTextContent(), formatShellToolResultForLog() (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.1
Nodes (20): accumulateUsage(), asErrorText(), asRecord(), collectAssistantText(), collectMessageText(), describeClaudeFailure(), describeGeminiFailure(), detectClaudeLoginRequired() (+12 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (12): asString(), buildMarkdown(), isEmptyObject(), isPathDefault(), isPlainRecord(), normalizePortableConfig(), normalizePortableEnv(), pruneDefaultLikeValue() (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (12): deriveCommentId(), deriveTaskKey(), describeSessionResetReason(), enrichWakeContextSnapshot(), mergeCoalescedContextSnapshot(), normalizeSessionParams(), readNonEmptyString(), resolveNextSessionState() (+4 more)

### Community 19 - "Community 19"
Cohesion: 0.09
Nodes (7): isScopeKind(), looksLikePath(), parseScopeKey(), pushRecord(), resolveWorkspace(), runCuratedCommand(), sanitizeWorkspacePath()

### Community 20 - "Community 20"
Cohesion: 0.23
Nodes (20): asNumber(), asRecord(), asString(), errorText(), extractTextContent(), printAssistantMessage(), printCodexStreamEvent(), printCursorStreamEvent() (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.17
Nodes (20): collectDeploymentEnvRows(), defaultSecretsKeyFilePath(), defaultStorageBaseDir(), ensureAgentJwtSecret(), envCommand(), isNonEmpty(), loadAgentJwtEnvFile(), loadPaperclipEnvFile() (+12 more)

### Community 22 - "Community 22"
Cohesion: 0.2
Nodes (17): dedupeModels(), discoverOpenCodeModels(), discoverOpenCodeModelsCached(), discoverPiModels(), discoverPiModelsCached(), discoveryCacheKey(), ensureOpenCodeModelConfiguredAndAvailable(), ensurePiModelConfiguredAndAvailable() (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.26
Nodes (19): buildActivityToast(), buildAgentStatusToast(), buildJoinRequestToast(), buildRunStatusToast(), describeIssueUpdate(), gatedPushToast(), handleLiveEvent(), invalidateActivityQueries() (+11 more)

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (6): _load_cron_jobs_tool(), Direct unit tests for cron-jobs-tool.py sync logic, Tests for sync-cron-jobs.sh, Legacy row with same name as a repo job must not double-schedule., TestCronJobsToolSync, TestSyncCronJobsScript

### Community 25 - "Community 25"
Cohesion: 0.2
Nodes (4): _load_audit_module(), Direct unit tests for _workflow_health_audit.py audit() function., WorkflowHealthAuditDirectTests, _write_minimal_repo()

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (14): apply_line_removals(), _iter_jsonl_records(), LineAction, main(), orphan_started_indices(), parse_ts(), plan_cleanup(), Latest record per job (any status) is \"started\" and older than grace. (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.18
Nodes (14): findCompanyByPrefix(), getRememberedPathOwnerCompanyId(), isRememberableCompanyPath(), sanitizeRememberedPathForCompany(), applyCompanyPrefix(), extractCompanyPrefixFromPath(), getRootSegment(), isBoardPathWithoutPrefix() (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.22
Nodes (18): applyUiBranding(), createFaviconDataUrl(), deriveColorFromSeed(), escapeHtmlAttribute(), getWorktreeUiBranding(), hexToRgb(), hslComponentToHex(), hslToHex() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (6): AlertMessageFormattingTests, DraftFormattingTests, HumanLabelCoverageTests, Ensure health alerts sent to Telegram are human-readable, not internal codes., Ensure Linear drafts use human labels, not internal codes., Every remediation hint must have a corresponding human label.

### Community 30 - "Community 30"
Cohesion: 0.16
Nodes (12): cancel_issue(), find_open_workflow_health_issues(), graphql(), main(), pending_workflow_health_drafts(), plan_and_apply(), Return issue nodes {id, identifier, title} that are still open., reset_workflow_health_state() (+4 more)

### Community 31 - "Community 31"
Cohesion: 0.12
Nodes (2): JsonRpcCallError, JsonRpcParseError

### Community 32 - "Community 32"
Cohesion: 0.26
Nodes (15): append_jsonl(), calculate_brier(), calculate_max_drawdown(), current_bankroll(), filter_recent(), jsonl_path(), load_jsonl(), load_promotion_alert_state() (+7 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (8): buildWorktreeConfig(), generateWorktreeColor(), hslComponentToHex(), hslToHex(), isLoopbackHost(), nonEmpty(), resolveSuggestedWorktreeName(), rewriteLocalUrlPort()

### Community 34 - "Community 34"
Cohesion: 0.27
Nodes (15): asPositiveInt(), expandHomePrefix(), findConfigFileFromAncestors(), migrateLegacyConfig(), parseEnvFile(), readConfig(), readEnvEntries(), resolveDatabaseTarget() (+7 more)

### Community 35 - "Community 35"
Cohesion: 0.25
Nodes (15): has_matching_open_linear_issue(), has_matching_open_pr(), has_matching_pending_draft(), main(), _norm(), post_health_alert(), Hash workflow+kind pairs, ignoring timestamps in messages.      The old approach, read_state() (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.32
Nodes (15): call_script(), ensure_alpha_polymarket(), ensure_daily_brief(), ensure_openclaw_research(), first_headline(), has_audit_event(), has_recent_alpha_report(), load_audit_events() (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.27
Nodes (1): CronRunRecordTests

### Community 38 - "Community 38"
Cohesion: 0.12
Nodes (1): PolymarketTradeTests

### Community 39 - "Community 39"
Cohesion: 0.29
Nodes (14): defaultHomeDirs(), defaultUserNames(), escapeRegExp(), getDefaultCurrentUserCandidates(), isPlainObject(), redactCurrentUserText(), redactCurrentUserValue(), redactHomePathUserSegments() (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.27
Nodes (14): date_window(), fetch_paperclip_runs(), main(), _paperclip_auth_headers(), parse_args(), parse_ts(), read_cron_records(), render_text() (+6 more)

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (14): append_jsonl(), dedup_append(), format_recent_trades(), format_whale_accuracy(), ingest_decision(), ingest_result(), latest_from_file(), latest_resolved_result() (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.16
Nodes (3): compareIdentifiers(), compareSemver(), parseSemver()

### Community 43 - "Community 43"
Cohesion: 0.15
Nodes (2): normalizeSelector(), resolveCompanyForDeletion()

### Community 44 - "Community 44"
Cohesion: 0.31
Nodes (11): defaultClientContext(), findContextFileFromAncestors(), normalizeContext(), normalizeProfile(), parseJson(), readContext(), resolveContextPath(), setCurrentProfile() (+3 more)

### Community 45 - "Community 45"
Cohesion: 0.24
Nodes (10): drawStaticFrame(), handleVisibility(), spawnClip(), spriteSize(), stampClip(), startLoop(), step(), stopLoop() (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.24
Nodes (11): formatBackupSize(), formatDatabaseBackupResult(), normalizeNullifyColumnMap(), normalizeTableNameSet(), pruneOldBackups(), quoteIdentifier(), quoteQualifiedName(), runDatabaseBackup() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.18
Nodes (8): default_cron_path(), ensure_job_state_dicts(), main(), Ensure each job has ``state: {}`` when missing or not a dict. Returns (fixed_cou, Return (count_removed, job_names_touched)., strip_running_at_ms(), CronUnstickRunningTests, Tests for tools/_cron_unstick_running.py.

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (12): expandHomePrefix(), resolveDefaultAgentWorkspaceDir(), resolveDefaultBackupDir(), resolveDefaultConfigPath(), resolveDefaultEmbeddedPostgresDir(), resolveDefaultLogsDir(), resolveDefaultSecretsKeyFilePath(), resolveDefaultStorageDir() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.31
Nodes (9): collectFromJsonValue(), dedupeModels(), fetchCursorModelsFromCli(), isLikelyModelId(), listCursorModels(), mergedWithFallback(), parseCursorModelsOutput(), pushModelId() (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (6): buildPinnedRequestOptions(), executePinnedHttpRequest(), looksLikePath(), sanitizeWorkspaceName(), sanitizeWorkspacePath(), sanitizeWorkspaceText()

### Community 51 - "Community 51"
Cohesion: 0.4
Nodes (12): describeLocalInstancePaths(), expandHomePrefix(), resolveDefaultBackupDir(), resolveDefaultConfigPath(), resolveDefaultContextPath(), resolveDefaultEmbeddedPostgresDir(), resolveDefaultLogsDir(), resolveDefaultSecretsKeyFilePath() (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.35
Nodes (12): asPositiveInt(), expandHomePrefix(), main(), readConfig(), resolveBackupDir(), resolveConnectionString(), resolveDefaultBackupDir(), resolveDefaultConfigPath() (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.35
Nodes (12): CmdResult, extract_first_line(), github_latest_release(), latest_memory_highlights(), main(), npm_latest_openclaw(), openclaw_version(), post_headline() (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (2): CronCoreWorkflowRunTests, Stub non-zero exit (e.g. 124) as timeout/tool kill proxy; terminal record must s

### Community 55 - "Community 55"
Cohesion: 0.21
Nodes (5): _git_init(), Shell syntax validation for deploy-related scripts, Tests for self-deploy.sh, TestDeployScriptSyntax, TestSelfDeployScript

### Community 56 - "Community 56"
Cohesion: 0.24
Nodes (3): load_core_jobs_fixture(), Full agent transcripts exceed Telegram 4096; hourly summary uses telegram-post.s, WorkflowPromptTests

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (6): ApprovalWorkflowTests, Tests for the suggestion-to-linear draft approval workflow., approve-suggestion.sh --dry-run exits 0 with valid args., approve-suggestion.sh --dry-run prints draft request and inline approval steps., approve-suggestion.sh exits 1 when given insufficient args., approval-smoke.sh exits 0 and validates the workflow.

### Community 58 - "Community 58"
Cohesion: 0.42
Nodes (1): WorkflowHealthHandleTests

### Community 59 - "Community 59"
Cohesion: 0.27
Nodes (6): ensureUiDir(), getUiBuildSnapshot(), listFilesRecursive(), snapshotSignature(), startPluginDevServer(), startUiWatcher()

### Community 60 - "Community 60"
Cohesion: 0.35
Nodes (10): date_window(), main(), one_line(), parse_args(), read_events(), reasons_for_event(), render_report(), sort_key() (+2 more)

### Community 61 - "Community 61"
Cohesion: 0.29
Nodes (2): GrokClawDoctorTests, Set up a temp workspace with stubs for all doctor external deps.

### Community 62 - "Community 62"
Cohesion: 0.31
Nodes (1): CronPaperclipLifecycleTests

### Community 63 - "Community 63"
Cohesion: 0.2
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 0.4
Nodes (9): base64UrlDecode(), base64UrlEncode(), createLocalAgentJwt(), jwtConfig(), parseJson(), parseNumber(), safeCompare(), signPayload() (+1 more)

### Community 65 - "Community 65"
Cohesion: 0.2
Nodes (1): PluginSandboxError

### Community 66 - "Community 66"
Cohesion: 0.38
Nodes (9): formatError(), getMissingModuleSpecifier(), importServerEntry(), isModuleNotFoundError(), maybeEnableUiDevMiddleware(), resolveBootstrapInviteBaseUrl(), runCommand(), shouldGenerateBootstrapInviteAfterStart() (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.42
Nodes (9): ensureCopiedFile(), ensureParentDir(), ensureSymlink(), isWorktreeMode(), nonEmpty(), pathExists(), prepareWorktreeCodexHome(), resolveCodexHomeDir() (+1 more)

### Community 68 - "Community 68"
Cohesion: 0.44
Nodes (9): append_decision(), append_skip(), build_record(), evaluate_staged_candidate(), kelly_fraction(), main(), probability_yes(), record_explicit_skip() (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.4
Nodes (9): fetch_market(), get_winning_index(), get_winning_side(), main(), market_is_resolved(), parse_prices(), pnl(), WIN = (1/odds - 1) units; LOSS = -1 unit. (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.39
Nodes (6): getWorktreeUiBranding(), hexToRgb(), normalizeHexColor(), pickReadableTextColor(), readMetaContent(), relativeLuminanceChannel()

### Community 71 - "Community 71"
Cohesion: 0.22
Nodes (1): HttpError

### Community 72 - "Community 72"
Cohesion: 0.31
Nodes (4): buildObjectKey(), normalizeNamespace(), sanitizeSegment(), splitFilename()

### Community 73 - "Community 73"
Cohesion: 0.42
Nodes (8): advanceToNextMonth(), findNext(), nextCronTick(), nextCronTickFromExpression(), parseCron(), parseField(), validateBounds(), validateCron()

### Community 74 - "Community 74"
Cohesion: 0.42
Nodes (8): configExists(), findConfigFileFromAncestors(), formatValidationError(), migrateLegacyConfig(), parseJson(), readConfig(), resolveConfigPath(), writeConfig()

### Community 75 - "Community 75"
Cohesion: 0.33
Nodes (6): formatInlineRecord(), inferApiBaseFromConfig(), printOutput(), readKeyFromProfileEnv(), renderValue(), resolveCommandContext()

### Community 76 - "Community 76"
Cohesion: 0.25
Nodes (2): normalizeScope(), stateMapKey()

### Community 77 - "Community 77"
Cohesion: 0.42
Nodes (8): build_research_markdown(), clamp_open_probability(), CmdResult, main(), parse_json_maybe(), run_command(), safe_text(), utc_now()

### Community 78 - "Community 78"
Cohesion: 0.42
Nodes (1): LinearTicketLoggingTests

### Community 79 - "Community 79"
Cohesion: 0.39
Nodes (1): PolymarketDecideTests

### Community 80 - "Community 80"
Cohesion: 0.36
Nodes (1): AlphaPolymarketDeterministicTests

### Community 81 - "Community 81"
Cohesion: 0.36
Nodes (1): TelegramAuditLogTests

### Community 82 - "Community 82"
Cohesion: 0.43
Nodes (6): createBetterAuthInstance(), deriveAuthTrustedOrigins(), headersFromExpressRequest(), headersFromNodeHeaders(), resolveBetterAuthSession(), resolveBetterAuthSessionFromHeaders()

### Community 83 - "Community 83"
Cohesion: 0.36
Nodes (4): authorizeUpgrade(), hashToken(), headersFromIncomingMessage(), parseBearerToken()

### Community 84 - "Community 84"
Cohesion: 0.5
Nodes (6): dedupeModels(), fetchOpenAiModels(), fingerprint(), listCodexModels(), mergedWithFallback(), resolveOpenAiApiKey()

### Community 85 - "Community 85"
Cohesion: 0.39
Nodes (5): buildExecutionWorkspaceAdapterConfig(), cloneRecord(), parseExecutionWorkspaceStrategy(), parseIssueExecutionWorkspaceSettings(), parseProjectExecutionWorkspacePolicy()

### Community 86 - "Community 86"
Cohesion: 0.46
Nodes (7): canCreateBootstrapInviteImmediately(), onboard(), parseBooleanFromEnv(), parseEnumFromEnv(), parseNumberFromEnv(), quickstartDefaultsFromEnv(), resolvePathFromEnv()

### Community 87 - "Community 87"
Cohesion: 0.43
Nodes (7): ensure_cron_job_state_dicts(), load_json(), main(), merge_runtime_fields(), Preserve OpenClaw scheduler state when syncing from git; include orphan old jobs, Mutate store so every job has ``state`` as a dict.      OpenClaw's cron ``start(, validate_jobs()

### Community 88 - "Community 88"
Cohesion: 0.46
Nodes (7): main(), parse_args(), probe_http(), read_latest_runs(), render_text(), run_kpi_report(), workspace_root()

### Community 89 - "Community 89"
Cohesion: 0.43
Nodes (7): build_payload(), digest_already_recorded(), digest_week_key(), load_recent_results(), main(), mark_digest_recorded(), parse_result_date()

### Community 90 - "Community 90"
Cohesion: 0.36
Nodes (1): PrReviewInfrastructureTests

### Community 91 - "Community 91"
Cohesion: 0.48
Nodes (5): hashString(), hexToHue(), hslToRgb(), makeCompanyPatternDataUrl(), mulberry32()

### Community 92 - "Community 92"
Cohesion: 0.29
Nodes (0): 

### Community 93 - "Community 93"
Cohesion: 0.29
Nodes (0): 

### Community 94 - "Community 94"
Cohesion: 0.43
Nodes (5): claimBoardOwnership(), createChallenge(), getChallengeStatus(), initializeBoardClaimChallenge(), inspectBoardClaimChallenge()

### Community 95 - "Community 95"
Cohesion: 0.76
Nodes (6): isPlainBinding(), isPlainObject(), isSecretRefBinding(), redactEventPayload(), sanitizeRecord(), sanitizeValue()

### Community 96 - "Community 96"
Cohesion: 0.38
Nodes (3): normalizeAllowedHostnames(), privateHostnameGuard(), resolvePrivateHostnameAllowSet()

### Community 97 - "Community 97"
Cohesion: 0.52
Nodes (6): decide(), main(), parse_args(), render_text(), run_kpis(), workspace_root()

### Community 98 - "Community 98"
Cohesion: 0.57
Nodes (6): backend_script(), ensure_backend_state(), main(), mempalace_health_check(), now_iso(), run_backend()

### Community 99 - "Community 99"
Cohesion: 0.48
Nodes (1): CronWorkflowEvidenceTests

### Community 100 - "Community 100"
Cohesion: 0.43
Nodes (1): LinearDraftApprovalTests

### Community 101 - "Community 101"
Cohesion: 0.43
Nodes (1): HealthCheckTests

### Community 102 - "Community 102"
Cohesion: 0.29
Nodes (1): PolymarketMetricsTests

### Community 103 - "Community 103"
Cohesion: 0.67
Nodes (5): color(), printStartupBanner(), redactConnectionString(), resolveAgentJwtSecretStatus(), row()

### Community 104 - "Community 104"
Cohesion: 0.4
Nodes (2): createS3StorageProvider(), normalizePrefix()

### Community 105 - "Community 105"
Cohesion: 0.33
Nodes (0): 

### Community 106 - "Community 106"
Cohesion: 0.47
Nodes (3): publishGlobalLiveEvent(), publishLiveEvent(), toLiveEvent()

### Community 107 - "Community 107"
Cohesion: 0.67
Nodes (5): doctor(), maybeRepair(), printResult(), printSummary(), runRepairableCheck()

### Community 108 - "Community 108"
Cohesion: 0.6
Nodes (5): bootstrapCeoInvite(), createInviteToken(), hashToken(), resolveBaseUrl(), resolveDbUrl()

### Community 109 - "Community 109"
Cohesion: 0.53
Nodes (4): asErrorText(), asRecord(), heartbeatRun(), safeParseLogLine()

### Community 110 - "Community 110"
Cohesion: 0.33
Nodes (0): 

### Community 111 - "Community 111"
Cohesion: 0.33
Nodes (0): 

### Community 112 - "Community 112"
Cohesion: 0.6
Nodes (5): ensureEmbeddedPostgresConnection(), loadEmbeddedPostgresCtor(), readPidFilePort(), readRunningPostmasterPid(), resolveMigrationConnection()

### Community 113 - "Community 113"
Cohesion: 0.47
Nodes (1): GrokOpenclawResearchDeterministicTests

### Community 114 - "Community 114"
Cohesion: 0.33
Nodes (1): PolymarketDigestTests

### Community 115 - "Community 115"
Cohesion: 0.47
Nodes (1): PrReviewWatchTests

### Community 116 - "Community 116"
Cohesion: 0.47
Nodes (1): RunOpenClawAgentTests

### Community 117 - "Community 117"
Cohesion: 0.47
Nodes (1): CronOpenclawAgentTests

### Community 118 - "Community 118"
Cohesion: 0.47
Nodes (1): DispatchActionLinearDraftTests

### Community 119 - "Community 119"
Cohesion: 0.47
Nodes (1): CleanupPendingWorkflowHealthDraftsTests

### Community 120 - "Community 120"
Cohesion: 0.47
Nodes (1): SchedulerSimplificationGateTests

### Community 121 - "Community 121"
Cohesion: 0.47
Nodes (1): CronWorkflowLayersTests

### Community 122 - "Community 122"
Cohesion: 0.53
Nodes (2): _load_module(), TelegramPostTests

### Community 123 - "Community 123"
Cohesion: 0.47
Nodes (1): GatewayWatchdogTests

### Community 124 - "Community 124"
Cohesion: 0.47
Nodes (1): HealthScheduleTests

### Community 125 - "Community 125"
Cohesion: 0.53
Nodes (2): _load_audit_module(), WorkflowHealthAuditTests

### Community 126 - "Community 126"
Cohesion: 0.4
Nodes (0): 

### Community 127 - "Community 127"
Cohesion: 0.6
Nodes (3): isTrustedBoardMutationRequest(), parseOrigin(), trustedOriginsForRequest()

### Community 128 - "Community 128"
Cohesion: 0.5
Nodes (2): normalizeObjectKey(), resolveWithin()

### Community 129 - "Community 129"
Cohesion: 0.4
Nodes (0): 

### Community 130 - "Community 130"
Cohesion: 0.5
Nodes (2): createLocalFileRunLogStore(), getRunLogStore()

### Community 131 - "Community 131"
Cohesion: 0.7
Nodes (4): dbBackupCommand(), normalizeRetentionDays(), resolveBackupDir(), resolveConnectionString()

### Community 132 - "Community 132"
Cohesion: 0.4
Nodes (0): 

### Community 133 - "Community 133"
Cohesion: 0.4
Nodes (1): CapabilityDeniedError

### Community 134 - "Community 134"
Cohesion: 0.8
Nodes (4): getBridgeRegistry(), getSdkUiRuntimeValue(), missingBridgeValueError(), renderSdkUiComponent()

### Community 135 - "Community 135"
Cohesion: 0.7
Nodes (4): buildProjectMentionHref(), extractProjectMentionIds(), normalizeHexColor(), parseProjectMentionHref()

### Community 136 - "Community 136"
Cohesion: 0.7
Nodes (4): build_payload(), main(), request_timeout_seconds(), truncate_for_telegram()

### Community 137 - "Community 137"
Cohesion: 0.5
Nodes (1): CronWorkflowLayersE2ETests

### Community 138 - "Community 138"
Cohesion: 0.4
Nodes (1): PreCommitHookTests

### Community 139 - "Community 139"
Cohesion: 0.4
Nodes (1): NorthStarDocTests

### Community 140 - "Community 140"
Cohesion: 0.4
Nodes (1): PolymarketResolveTests

### Community 141 - "Community 141"
Cohesion: 0.4
Nodes (1): TelegramAuditReportTests

### Community 142 - "Community 142"
Cohesion: 0.4
Nodes (1): DispatchActionIdempotencyTests

### Community 143 - "Community 143"
Cohesion: 0.5
Nodes (1): CtoKpiReportTests

### Community 144 - "Community 144"
Cohesion: 0.5
Nodes (1): CtoStatusTests

### Community 145 - "Community 145"
Cohesion: 0.67
Nodes (2): isAllowedContentType(), matchesContentType()

### Community 146 - "Community 146"
Cohesion: 0.83
Nodes (3): findConfigFileFromAncestors(), resolvePaperclipConfigPath(), resolvePaperclipEnvPath()

### Community 147 - "Community 147"
Cohesion: 0.67
Nodes (2): createTempRepo(), runGit()

### Community 148 - "Community 148"
Cohesion: 0.5
Nodes (0): 

### Community 149 - "Community 149"
Cohesion: 0.5
Nodes (0): 

### Community 150 - "Community 150"
Cohesion: 0.5
Nodes (0): 

### Community 151 - "Community 151"
Cohesion: 0.83
Nodes (3): readNumericField(), summarizeHeartbeatRunResultJson(), truncateSummaryText()

### Community 152 - "Community 152"
Cohesion: 0.5
Nodes (0): 

### Community 153 - "Community 153"
Cohesion: 1.0
Nodes (3): defaultStorageBaseDir(), defaultStorageConfig(), promptStorage()

### Community 154 - "Community 154"
Cohesion: 0.5
Nodes (0): 

### Community 155 - "Community 155"
Cohesion: 0.67
Nodes (2): deriveAgentUrlKey(), normalizeAgentUrlKey()

### Community 156 - "Community 156"
Cohesion: 0.83
Nodes (3): append_retry_telemetry(), classify_failure(), main()

### Community 157 - "Community 157"
Cohesion: 0.5
Nodes (2): button_display_label(), Label shown on the button (clean, no token).

### Community 158 - "Community 158"
Cohesion: 0.67
Nodes (0): 

### Community 159 - "Community 159"
Cohesion: 0.67
Nodes (0): 

### Community 160 - "Community 160"
Cohesion: 1.0
Nodes (2): attachErrorContext(), errorHandler()

### Community 161 - "Community 161"
Cohesion: 0.67
Nodes (0): 

### Community 162 - "Community 162"
Cohesion: 0.67
Nodes (0): 

### Community 163 - "Community 163"
Cohesion: 0.67
Nodes (0): 

### Community 164 - "Community 164"
Cohesion: 0.67
Nodes (0): 

### Community 165 - "Community 165"
Cohesion: 0.67
Nodes (0): 

### Community 166 - "Community 166"
Cohesion: 1.0
Nodes (2): defaultPermissionsForRole(), normalizeAgentPermissions()

### Community 167 - "Community 167"
Cohesion: 0.67
Nodes (0): 

### Community 168 - "Community 168"
Cohesion: 0.67
Nodes (0): 

### Community 169 - "Community 169"
Cohesion: 0.67
Nodes (0): 

### Community 170 - "Community 170"
Cohesion: 0.67
Nodes (0): 

### Community 171 - "Community 171"
Cohesion: 1.0
Nodes (2): prunePluginLogs(), startPluginLogRetention()

### Community 172 - "Community 172"
Cohesion: 0.67
Nodes (0): 

### Community 173 - "Community 173"
Cohesion: 0.67
Nodes (0): 

### Community 174 - "Community 174"
Cohesion: 1.0
Nodes (2): normalizeHostnameInput(), parseHostnameCsv()

### Community 175 - "Community 175"
Cohesion: 1.0
Nodes (2): deploymentAuthCheck(), isLoopbackHost()

### Community 176 - "Community 176"
Cohesion: 1.0
Nodes (2): resolveRuntimeLikePath(), unique()

### Community 177 - "Community 177"
Cohesion: 0.67
Nodes (0): 

### Community 178 - "Community 178"
Cohesion: 1.0
Nodes (2): configure(), defaultConfig()

### Community 179 - "Community 179"
Cohesion: 1.0
Nodes (2): main(), parseArg()

### Community 180 - "Community 180"
Cohesion: 1.0
Nodes (2): runWorker(), startWorkerRpcHost()

### Community 181 - "Community 181"
Cohesion: 1.0
Nodes (2): deriveProjectUrlKey(), normalizeProjectUrlKey()

### Community 182 - "Community 182"
Cohesion: 0.67
Nodes (0): 

### Community 183 - "Community 183"
Cohesion: 0.67
Nodes (0): 

### Community 184 - "Community 184"
Cohesion: 1.0
Nodes (2): main(), utc_now()

### Community 185 - "Community 185"
Cohesion: 0.67
Nodes (2): compact_title(), Return a concise PR-style one-liner title.

### Community 186 - "Community 186"
Cohesion: 1.0
Nodes (0): 

### Community 187 - "Community 187"
Cohesion: 1.0
Nodes (0): 

### Community 188 - "Community 188"
Cohesion: 1.0
Nodes (0): 

### Community 189 - "Community 189"
Cohesion: 1.0
Nodes (0): 

### Community 190 - "Community 190"
Cohesion: 1.0
Nodes (0): 

### Community 191 - "Community 191"
Cohesion: 1.0
Nodes (0): 

### Community 192 - "Community 192"
Cohesion: 1.0
Nodes (0): 

### Community 193 - "Community 193"
Cohesion: 1.0
Nodes (0): 

### Community 194 - "Community 194"
Cohesion: 1.0
Nodes (0): 

### Community 195 - "Community 195"
Cohesion: 1.0
Nodes (0): 

### Community 196 - "Community 196"
Cohesion: 1.0
Nodes (0): 

### Community 197 - "Community 197"
Cohesion: 1.0
Nodes (0): 

### Community 198 - "Community 198"
Cohesion: 1.0
Nodes (0): 

### Community 199 - "Community 199"
Cohesion: 1.0
Nodes (0): 

### Community 200 - "Community 200"
Cohesion: 1.0
Nodes (0): 

### Community 201 - "Community 201"
Cohesion: 1.0
Nodes (0): 

### Community 202 - "Community 202"
Cohesion: 1.0
Nodes (0): 

### Community 203 - "Community 203"
Cohesion: 1.0
Nodes (0): 

### Community 204 - "Community 204"
Cohesion: 1.0
Nodes (0): 

### Community 205 - "Community 205"
Cohesion: 1.0
Nodes (0): 

### Community 206 - "Community 206"
Cohesion: 1.0
Nodes (0): 

### Community 207 - "Community 207"
Cohesion: 1.0
Nodes (0): 

### Community 208 - "Community 208"
Cohesion: 1.0
Nodes (0): 

### Community 209 - "Community 209"
Cohesion: 1.0
Nodes (0): 

### Community 210 - "Community 210"
Cohesion: 1.0
Nodes (0): 

### Community 211 - "Community 211"
Cohesion: 1.0
Nodes (0): 

### Community 212 - "Community 212"
Cohesion: 1.0
Nodes (0): 

### Community 213 - "Community 213"
Cohesion: 1.0
Nodes (0): 

### Community 214 - "Community 214"
Cohesion: 1.0
Nodes (0): 

### Community 215 - "Community 215"
Cohesion: 1.0
Nodes (0): 

### Community 216 - "Community 216"
Cohesion: 1.0
Nodes (0): 

### Community 217 - "Community 217"
Cohesion: 1.0
Nodes (0): 

### Community 218 - "Community 218"
Cohesion: 1.0
Nodes (0): 

### Community 219 - "Community 219"
Cohesion: 1.0
Nodes (0): 

### Community 220 - "Community 220"
Cohesion: 1.0
Nodes (0): 

### Community 221 - "Community 221"
Cohesion: 1.0
Nodes (0): 

### Community 222 - "Community 222"
Cohesion: 1.0
Nodes (0): 

### Community 223 - "Community 223"
Cohesion: 1.0
Nodes (0): 

### Community 224 - "Community 224"
Cohesion: 1.0
Nodes (0): 

### Community 225 - "Community 225"
Cohesion: 1.0
Nodes (0): 

### Community 226 - "Community 226"
Cohesion: 1.0
Nodes (0): 

### Community 227 - "Community 227"
Cohesion: 1.0
Nodes (0): 

### Community 228 - "Community 228"
Cohesion: 1.0
Nodes (0): 

### Community 229 - "Community 229"
Cohesion: 1.0
Nodes (0): 

### Community 230 - "Community 230"
Cohesion: 1.0
Nodes (0): 

### Community 231 - "Community 231"
Cohesion: 1.0
Nodes (0): 

### Community 232 - "Community 232"
Cohesion: 1.0
Nodes (0): 

### Community 233 - "Community 233"
Cohesion: 1.0
Nodes (0): 

### Community 234 - "Community 234"
Cohesion: 1.0
Nodes (0): 

### Community 235 - "Community 235"
Cohesion: 1.0
Nodes (0): 

### Community 236 - "Community 236"
Cohesion: 1.0
Nodes (0): 

### Community 237 - "Community 237"
Cohesion: 1.0
Nodes (0): 

### Community 238 - "Community 238"
Cohesion: 1.0
Nodes (0): 

### Community 239 - "Community 239"
Cohesion: 1.0
Nodes (0): 

### Community 240 - "Community 240"
Cohesion: 1.0
Nodes (0): 

### Community 241 - "Community 241"
Cohesion: 1.0
Nodes (0): 

### Community 242 - "Community 242"
Cohesion: 1.0
Nodes (0): 

### Community 243 - "Community 243"
Cohesion: 1.0
Nodes (0): 

### Community 244 - "Community 244"
Cohesion: 1.0
Nodes (0): 

### Community 245 - "Community 245"
Cohesion: 1.0
Nodes (0): 

### Community 246 - "Community 246"
Cohesion: 1.0
Nodes (0): 

### Community 247 - "Community 247"
Cohesion: 1.0
Nodes (0): 

### Community 248 - "Community 248"
Cohesion: 1.0
Nodes (0): 

### Community 249 - "Community 249"
Cohesion: 1.0
Nodes (0): 

### Community 250 - "Community 250"
Cohesion: 1.0
Nodes (0): 

### Community 251 - "Community 251"
Cohesion: 1.0
Nodes (0): 

### Community 252 - "Community 252"
Cohesion: 1.0
Nodes (0): 

### Community 253 - "Community 253"
Cohesion: 1.0
Nodes (0): 

### Community 254 - "Community 254"
Cohesion: 1.0
Nodes (0): 

### Community 255 - "Community 255"
Cohesion: 1.0
Nodes (0): 

### Community 256 - "Community 256"
Cohesion: 1.0
Nodes (0): 

### Community 257 - "Community 257"
Cohesion: 1.0
Nodes (0): 

### Community 258 - "Community 258"
Cohesion: 1.0
Nodes (0): 

### Community 259 - "Community 259"
Cohesion: 1.0
Nodes (0): 

### Community 260 - "Community 260"
Cohesion: 1.0
Nodes (0): 

### Community 261 - "Community 261"
Cohesion: 1.0
Nodes (0): 

### Community 262 - "Community 262"
Cohesion: 1.0
Nodes (0): 

### Community 263 - "Community 263"
Cohesion: 1.0
Nodes (0): 

### Community 264 - "Community 264"
Cohesion: 1.0
Nodes (0): 

### Community 265 - "Community 265"
Cohesion: 1.0
Nodes (0): 

### Community 266 - "Community 266"
Cohesion: 1.0
Nodes (0): 

### Community 267 - "Community 267"
Cohesion: 1.0
Nodes (0): 

### Community 268 - "Community 268"
Cohesion: 1.0
Nodes (0): 

### Community 269 - "Community 269"
Cohesion: 1.0
Nodes (0): 

### Community 270 - "Community 270"
Cohesion: 1.0
Nodes (0): 

### Community 271 - "Community 271"
Cohesion: 1.0
Nodes (0): 

### Community 272 - "Community 272"
Cohesion: 1.0
Nodes (0): 

### Community 273 - "Community 273"
Cohesion: 1.0
Nodes (0): 

### Community 274 - "Community 274"
Cohesion: 1.0
Nodes (0): 

### Community 275 - "Community 275"
Cohesion: 1.0
Nodes (0): 

### Community 276 - "Community 276"
Cohesion: 1.0
Nodes (0): 

### Community 277 - "Community 277"
Cohesion: 1.0
Nodes (0): 

### Community 278 - "Community 278"
Cohesion: 1.0
Nodes (0): 

### Community 279 - "Community 279"
Cohesion: 1.0
Nodes (0): 

### Community 280 - "Community 280"
Cohesion: 1.0
Nodes (0): 

### Community 281 - "Community 281"
Cohesion: 1.0
Nodes (0): 

### Community 282 - "Community 282"
Cohesion: 1.0
Nodes (0): 

### Community 283 - "Community 283"
Cohesion: 1.0
Nodes (0): 

### Community 284 - "Community 284"
Cohesion: 1.0
Nodes (0): 

### Community 285 - "Community 285"
Cohesion: 1.0
Nodes (0): 

### Community 286 - "Community 286"
Cohesion: 1.0
Nodes (0): 

### Community 287 - "Community 287"
Cohesion: 1.0
Nodes (0): 

### Community 288 - "Community 288"
Cohesion: 1.0
Nodes (0): 

### Community 289 - "Community 289"
Cohesion: 1.0
Nodes (0): 

### Community 290 - "Community 290"
Cohesion: 1.0
Nodes (0): 

### Community 291 - "Community 291"
Cohesion: 1.0
Nodes (0): 

### Community 292 - "Community 292"
Cohesion: 1.0
Nodes (0): 

### Community 293 - "Community 293"
Cohesion: 1.0
Nodes (0): 

### Community 294 - "Community 294"
Cohesion: 1.0
Nodes (0): 

### Community 295 - "Community 295"
Cohesion: 1.0
Nodes (0): 

### Community 296 - "Community 296"
Cohesion: 1.0
Nodes (0): 

### Community 297 - "Community 297"
Cohesion: 1.0
Nodes (0): 

### Community 298 - "Community 298"
Cohesion: 1.0
Nodes (0): 

### Community 299 - "Community 299"
Cohesion: 1.0
Nodes (0): 

### Community 300 - "Community 300"
Cohesion: 1.0
Nodes (0): 

### Community 301 - "Community 301"
Cohesion: 1.0
Nodes (0): 

### Community 302 - "Community 302"
Cohesion: 1.0
Nodes (0): 

### Community 303 - "Community 303"
Cohesion: 1.0
Nodes (0): 

### Community 304 - "Community 304"
Cohesion: 1.0
Nodes (0): 

### Community 305 - "Community 305"
Cohesion: 1.0
Nodes (0): 

### Community 306 - "Community 306"
Cohesion: 1.0
Nodes (0): 

### Community 307 - "Community 307"
Cohesion: 1.0
Nodes (0): 

### Community 308 - "Community 308"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **42 isolated node(s):** `Return set of market_id we've already decided/traded in last N days (avoids repe`, `True if market question/description matches geopolitical or crypto (word-boundar`, `Volume fallback: highest-volume geopolitical/crypto market closing within 7 days`, `Select best market from whale top traders' positions. Only geopolitical + crypto`, `Copy late-stage high-probability positions from known bonding wallets.` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 186`** (2 nodes): `config-file.ts`, `readConfigFile()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 187`** (2 nodes): `validate.ts`, `validate()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 188`** (2 nodes): `logger.ts`, `resolveServerLogDir()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 189`** (2 nodes): `provider-registry.ts`, `createStorageProviderFromConfig()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 190`** (2 nodes): `issues-user-context.test.ts`, `makeIssue()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 191`** (2 nodes): `invite-onboarding-text.test.ts`, `buildReq()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 192`** (2 nodes): `board-mutation-guard.test.ts`, `createApp()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 193`** (2 nodes): `hire-hook.test.ts`, `mockDbWithAgent()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 194`** (2 nodes): `heartbeat-workspace-session.test.ts`, `buildResolvedWorkspace()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 195`** (2 nodes): `approval-routes-idempotency.test.ts`, `createApp()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 196`** (2 nodes): `plugin-dev-watcher.test.ts`, `makeTempPluginDir()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 197`** (2 nodes): `private-hostname-guard.test.ts`, `createApp()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 198`** (2 nodes): `activity-routes.test.ts`, `createApp()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 199`** (2 nodes): `storage-local-provider.test.ts`, `readStreamToBuffer()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 200`** (2 nodes): `issues-checkout-wakeup.ts`, `shouldWakeAssigneeOnCheckout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 201`** (2 nodes): `hire-hook.ts`, `notifyHireApproved()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 202`** (2 nodes): `issue_approvals.ts`, `issueApprovalService()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 203`** (2 nodes): `plugin-job-scheduler.ts`, `createPluginJobScheduler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 204`** (2 nodes): `plugin-host-service-cleanup.ts`, `createPluginHostServiceCleanup()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 205`** (2 nodes): `plugin-config-validator.ts`, `validateInstanceConfig()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 206`** (2 nodes): `plugin-tool-dispatcher.ts`, `createPluginToolDispatcher()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 207`** (2 nodes): `plugin-job-coordinator.ts`, `createPluginJobCoordinator()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 208`** (2 nodes): `plugin-manifest-validator.ts`, `pluginManifestValidator()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 209`** (2 nodes): `plugin-job-store.ts`, `pluginJobStore()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 210`** (2 nodes): `plugin-tool-registry.ts`, `createPluginToolRegistry()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (2 nodes): `plugin-capability-validator.ts`, `pluginCapabilityValidator()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 212`** (2 nodes): `data-dir.ts`, `applyDataDirOverride()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 213`** (2 nodes): `storage-check.ts`, `storageCheck()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 214`** (2 nodes): `config-check.ts`, `configCheck()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 215`** (2 nodes): `llm-check.ts`, `llmCheck()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 216`** (2 nodes): `port-check.ts`, `portCheck()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 217`** (2 nodes): `log-check.ts`, `logCheck()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 218`** (2 nodes): `database-check.ts`, `databaseCheck()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 219`** (2 nodes): `banner.ts`, `printPaperclipCliBanner()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 220`** (2 nodes): `net.ts`, `checkPort()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 221`** (2 nodes): `common.test.ts`, `createTempPath()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 222`** (2 nodes): `context.test.ts`, `createTempContextPath()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 223`** (2 nodes): `company-delete.test.ts`, `makeCompany()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 224`** (2 nodes): `worktree.test.ts`, `buildSourceConfig()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 225`** (2 nodes): `doctor.test.ts`, `createTempConfig()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 226`** (2 nodes): `agent-jwt-env.test.ts`, `tempConfigPath()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 227`** (2 nodes): `llm.ts`, `promptLlm()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (2 nodes): `database.ts`, `promptDatabase()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (2 nodes): `logging.ts`, `promptLogging()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (2 nodes): `allowed-hostname.ts`, `addAllowedHostname()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (2 nodes): `define-plugin.ts`, `definePlugin()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (2 nodes): `bundlers.ts`, `createPluginBundlerPresets()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (2 nodes): `components.ts`, `createSdkUiComponent()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (2 nodes): `trust.ts`, `hasCursorTrustBypassArg()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (2 nodes): `migrate.ts`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (2 nodes): `migration-status.ts`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 237`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 238`** (1 nodes): `sw.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 239`** (1 nodes): `express.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 240`** (1 nodes): `log-redaction.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 241`** (1 nodes): `ui-branding.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 242`** (1 nodes): `project-shortname-resolution.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 243`** (1 nodes): `heartbeat-run-summary.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 244`** (1 nodes): `companies-route-path-guard.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 245`** (1 nodes): `paperclip-env.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 246`** (1 nodes): `agent-shortname-collision.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 247`** (1 nodes): `documents.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `agent-auth-jwt.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 249`** (1 nodes): `invite-accept-replay.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (1 nodes): `execution-workspace-policy.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 251`** (1 nodes): `invite-accept-gateway-defaults.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 252`** (1 nodes): `redaction.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 253`** (1 nodes): `invite-expiry.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (1 nodes): `plugin-worker-manager.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 255`** (1 nodes): `attachment-types.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 256`** (1 nodes): `invite-join-manager.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 257`** (1 nodes): `issues-checkout-wakeup.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 258`** (1 nodes): `issue-goal-fallback.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 259`** (1 nodes): `health.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 260`** (1 nodes): `schema.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 261`** (1 nodes): `http.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 262`** (1 nodes): `home-paths.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `data-dir.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 264`** (1 nodes): `manifest.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 265`** (1 nodes): `constants.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 266`** (1 nodes): `api.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 267`** (1 nodes): `config-schema.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 268`** (1 nodes): `project.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 269`** (1 nodes): `cost.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 270`** (1 nodes): `goal.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 271`** (1 nodes): `live.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 272`** (1 nodes): `asset.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 273`** (1 nodes): `models.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 274`** (1 nodes): `parse.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 275`** (1 nodes): `drizzle.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 276`** (1 nodes): `seed.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 277`** (1 nodes): `workspace_runtime_services.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 278`** (1 nodes): `issue_attachments.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 279`** (1 nodes): `agent_config_revisions.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 280`** (1 nodes): `plugin_company_settings.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 281`** (1 nodes): `principal_permission_grants.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 282`** (1 nodes): `plugin_entities.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 283`** (1 nodes): `project_workspaces.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 284`** (1 nodes): `plugin_webhooks.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 285`** (1 nodes): `agent_wakeup_requests.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 286`** (1 nodes): `join_requests.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 287`** (1 nodes): `agent_api_keys.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 288`** (1 nodes): `plugin_config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 289`** (1 nodes): `project_goals.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 290`** (1 nodes): `approval_comments.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 291`** (1 nodes): `company_memberships.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 292`** (1 nodes): `document_revisions.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 293`** (1 nodes): `issue_comments.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 294`** (1 nodes): `heartbeat_run_events.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 295`** (1 nodes): `plugin_logs.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 296`** (1 nodes): `issue_documents.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 297`** (1 nodes): `instance_user_roles.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 298`** (1 nodes): `plugin_jobs.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 299`** (1 nodes): `issue_read_states.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 300`** (1 nodes): `issue_labels.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 301`** (1 nodes): `cost_events.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 302`** (1 nodes): `agent_task_sessions.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 303`** (1 nodes): `invites.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 304`** (1 nodes): `labels.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 305`** (1 nodes): `heartbeat_runs.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 306`** (1 nodes): `plugin_state.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 307`** (1 nodes): `agent_runtime_state.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 308`** (1 nodes): `_linear_transition.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Return set of market_id we've already decided/traded in last N days (avoids repe`, `True if market question/description matches geopolitical or crypto (word-boundar`, `Volume fallback: highest-volume geopolitical/crypto market closing within 7 days` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.04 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.04 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._