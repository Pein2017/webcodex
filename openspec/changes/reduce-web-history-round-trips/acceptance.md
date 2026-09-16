# Local acceptance — 2026-09-16

Status: lead-accepted, 6/6 tasks. This is local source acceptance, not a release
or browser acceptance. Baseline is the previous dirty accepted candidate on
coordexp/web-workflow at ab089186; all unrelated existing changes are preserved.

## Ownership and corrections

- Terra/high owned only plugin.mjs and plugin.test.mjs.
- Luna/medium owned the three named guidance/README files.
- Lead owned OpenSpec, interface decisions, source-diff inspection and independent
  diagnostics. No nested delegation or additional reviewer was used.
- Documentation correction: replace existing check/list wording in place rather
  than append conflicting guidance; distinguish bounded filename lookup from
  browsing unrelated history bodies and forward EOF from latest exhaustion.
- Initial worker RED: latest rejected and ten pages of a sparse forward fixture
  read 3,798,216 bytes. Initial candidate passed 27 tests but was not accepted.
- Lead found a concrete latest boundary failure: 15 valid records with 60,000-byte
  text returned only 13, losing m10 and m2. The worker added a RED regression and
  distinguished call-budget exhaustion from a demonstrated oversized record.
- Lead then reproduced and directly fixed the consequent BOF edge: a file
  containing only an unterminated 19-byte record repeated its latest cursor.
  The new test failed before the one-condition correction and now passes.

This task supports the value of bounded ownership and lead falsification; it
does not establish a model ranking or a total-cost improvement over prior work.

## Fresh lead checks

- `npm test --prefix plugins/web-workflow`: 29 passed, zero failures.
- `node --check plugins/web-workflow/plugin.mjs` and the corresponding test file:
  passed.
- `node /tmp/webcodex-roundtrip-baseline.xPlSXq/lead-check.mjs`: passed chronological
  latest pages, exact byte provenance, older snapshot pagination during append,
  fresh latest seeing new messages, public-only projection, a 122 MiB sparse
  tail in one call, partial append completion, all 15 long boundary messages,
  and the 100-message forward read bound. Fixtures are synthetic and disposable;
  no private bodies entered repository records.
- `git diff --check` and
  `openspec validate reduce-web-history-round-trips --strict`: passed.

## Matched I/O comparison

The lead ran the pre-task plugin copy and final candidate against the SAME
1000-record synthetic file (event_msg/user_message, IDs s0..s999, each text 400
ASCII characters), reading ten forward pages of ten messages through the plugin
protocol. Each run returned exactly 100 messages:

| Source | Reported total bytesRead |
| --- | ---: |
| Pre-task accepted plugin | 4,739,088 |
| Final candidate | 483,328 |

Reduction: 89.8012%. This measures bounded source I/O on this fixture, not browser
latency, model token use or overall throughput. The original sparse worker
fixture differs and must not be used as the denominator for this comparison.

## Boundaries and residual limits

Forward defaults and v2 cursors remain; latest uses tagged v3 snapshot cursors,
chronological messages per page and older-history continuation. Latest line
numbers are null, with exact byte offsets; fresh latest calls observe new appends.
Each call retains 512 KiB scan plus 16 KiB fingerprint limits. Sparse or oversized
history can require empty but advancing pages. The backward scanner can reread
delimiter windows within its fixed budget; no claim of minimal I/O in that mode.
Existing append-only identity and heuristic redaction limitations remain.

No code graph reindex, Rust protocol change, Cargo suite, dependency, persistent
cache, deployment, service restart, configuration activation, Git commit/push,
GPU task or research-worktree mutation occurred. The new mode is not yet exposed
by the deployed service/browser. Publishing and deployment require separate
authorization.
