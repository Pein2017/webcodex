use crate::*;
use webcodex_core::workflow_session_contract::SessionMode;

const PROJECT: &str = "agent:oe:baseline-fixture";
const HEAD: &str = "0123456789abcdef0123456789abcdef01234567";
const ROOT_KEY: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

fn request(resume_session_id: Option<String>) -> CodingSessionRequest {
    CodingSessionRequest {
        project: PROJECT.to_string(),
        authority_fingerprint: TEST_ONLY_PROJECT_SESSION_AUTHORITY_FINGERPRINT.to_string(),
        resume_session_id,
        instruction: Some("observe workspace".to_string()),
        mode: SessionMode::Normal,
        guards: SessionGuards::default(),
        execution_context: None,
        project_instructions: None,
        transport: SessionTransport::Api,
        context_refreshed: true,
        write_scope_verified: true,
    }
}

fn baseline(path: &str) -> WorkspaceBaseline {
    WorkspaceBaseline {
        project: PROJECT.to_string(),
        repository_key: ROOT_KEY.to_string(),
        head: Some(HEAD.to_string()),
        complete: true,
        files_total: Some(1),
        entries: vec![WorkspaceBaselineEntry {
            path: path.to_string(),
            status: "modified".to_string(),
        }],
    }
}

#[test]
fn workspace_baseline_is_immutable_across_resume_restart_and_missing_legacy() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("sessions.json");
    let store = SessionStore::with_persistence(path.clone(), 10, 10);
    let created = store
        .ensure_coding_session_with_baseline(request(None), Some(baseline("existing.txt")))
        .unwrap();
    let id = created.summary.session_id.clone();
    assert_eq!(
        created.summary.workspace_baseline,
        Some(baseline("existing.txt"))
    );
    let generic_summary = serde_json::to_value(&created.summary).unwrap();
    assert!(
        generic_summary.get("workspace_baseline").is_none(),
        "generic Session projection must not serialize internal paths/root hash"
    );
    let resumed = store
        .ensure_coding_session_with_baseline(
            request(Some(id.clone())),
            Some(baseline("replacement.txt")),
        )
        .unwrap();
    assert_eq!(
        resumed.summary.workspace_baseline,
        Some(baseline("existing.txt"))
    );

    store.flush_persistence();
    let raw = std::fs::read_to_string(&path).unwrap();
    assert!(raw.contains("existing.txt"));
    assert!(!raw.contains("replacement.txt"));
    let restored = SessionStore::with_persistence(path, 10, 10);
    assert_eq!(
        restored.summary(&id, None).unwrap().workspace_baseline,
        Some(baseline("existing.txt"))
    );

    let legacy = restored.ensure_coding_session(request(None)).unwrap();
    assert!(legacy.summary.workspace_baseline.is_none());
    let legacy_resumed = restored
        .ensure_coding_session_with_baseline(
            request(Some(legacy.summary.session_id)),
            Some(baseline("late.txt")),
        )
        .unwrap();
    assert!(
        legacy_resumed.summary.workspace_baseline.is_none(),
        "missing original baseline must not be recaptured"
    );
}

#[test]
fn workspace_baseline_rejects_oversized_and_unsafe_restore_metadata() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("sessions.json");
    let store = SessionStore::with_persistence(path.clone(), 10, 10);
    let invalid = WorkspaceBaseline {
        entries: vec![WorkspaceBaselineEntry {
            path: "x".repeat(4_097),
            status: "modified".to_string(),
        }],
        ..baseline("safe.txt")
    };
    let created = store
        .ensure_coding_session_with_baseline(request(None), Some(invalid))
        .unwrap();
    let retained_baseline = created.summary.workspace_baseline.unwrap();
    assert!(!retained_baseline.complete);
    assert!(retained_baseline.entries.is_empty());
    store.flush_persistence();
    assert!(!std::fs::read_to_string(&path)
        .unwrap()
        .contains(&"x".repeat(4_097)));
    let restored = SessionStore::with_persistence(path, 10, 10);
    let retained = restored
        .summary(&created.summary.session_id, None)
        .unwrap()
        .workspace_baseline
        .unwrap();
    assert!(!retained.complete);
    assert!(retained.entries.is_empty());

    let mismatched = WorkspaceBaseline {
        project: "other-target".to_string(),
        ..baseline("safe.txt")
    };
    let created = restored
        .ensure_coding_session_with_baseline(request(None), Some(mismatched))
        .unwrap();
    assert!(created
        .summary
        .workspace_baseline
        .unwrap()
        .entries
        .is_empty());

    let unsafe_root = WorkspaceBaseline {
        repository_key: "z".repeat(50_000),
        ..baseline("safe.txt")
    };
    let created = restored
        .ensure_coding_session_with_baseline(request(None), Some(unsafe_root))
        .unwrap();
    let retained = created.summary.workspace_baseline.unwrap();
    assert!(retained.entries.is_empty());
    assert_eq!(retained.repository_key.len(), 64);
}
