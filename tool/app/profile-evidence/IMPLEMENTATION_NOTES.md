# Local column mapping reuse boundary

Baseline commit: `ce355644e9a58165494b13f8192aee13dd09ef2e`. The complete pre-edit tool byte manifest is [BASELINE.json](BASELINE.json). This work changes only tool files and performs no Git writes or real model calls.

- Optional explicit file reuse, no automatic storage or network. Standalone `ab-column-profile`, internal version 1, 8KiB UTF-8 cap. Exact role keys, lowercase SHA-256 fingerprints of selected parsed headers or optional null; no raw headers, rows, IDs, filename, preview, arm labels, cohort names or condition evidence.
- Fingerprints are not anonymity guarantees. Candidate lookup matches the current parsed names exactly, independent of column order, and rejects unknown fields, duplicate object keys, invalid digests, unsupported format/mode, missing/duplicate names and invalid UTF-8 atomically.
- Successful import discards prepared/results/consents/print and inherited conditions/evidence. It renders current CSV names only, blanks raw arm labels, and leaves mapping/input confirmation false. Existing mapping confirmation and application are mandatory. Failures retain current data/result/conditions and candidates. Profile hashes never enter data lineage or project/report/model serializers.
- Only bounded CRM alias additions. Known observation aliases cannot be dropped, individual format stays individual, and IMMATURE_OBSERVATION remains an engine error. All rows are preserved; extra arm values reject conversion. Unknown semantic meanings remain the user's responsibility.
- The download link serves only a fixed synthetic fixture and does not modify the current input. Actual engine expected values are executed and logged, not a marketing winner claim.
- WebCrypto and Node webcrypto use actual SHA-256. Missing crypto or digest failure is visible and non-destructive. File reads and hashing share the existing input epoch/owner. Older finally blocks cannot unlock newer work. Tests delay real bytes/digest completion, not substitute fake hashes.
- The existing 160.16-second tutorial and caption/timeline bytes are preserved. It does not teach this new template control; no new video was recorded. Engines, schema7, legacy safeguards, R05/R06 gates and raw metadata shadows are preserved and rerun.

## Verification

The new standalone Node smoke groups and actual Chrome checks run in the full integration pipeline. Source SHA metadata, privacy/tutorial flags, fixture hashes and baseline preservation have negative guards. All existing semantic/help/conditions/print checks remain in the pipeline. Package membership is explicit and a fresh extraction runs the same full suite. Counts come from the new execution ledger, not a manually incremented claim. Source and extracted repetitions are not new unique coverage.

Initial standalone Node and Chrome runs passed. Any later initial failures are preserved in separate local logs and must be classified as a production fix or a test correction; a timing retry is not proof of a general performance fix. Automated synthetic checks are not human usability observations, independent security certification, live CRM outcomes or live model verification.
