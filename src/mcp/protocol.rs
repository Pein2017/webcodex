use serde::Deserialize;
use serde_json::{json, Value};

pub(super) const MCP_PROTOCOL_VERSION: &str = "2025-06-18";
pub(super) const MCP_CHATGPT_PROTOCOL_VERSION: &str = "2025-11-25";
pub(super) const MCP_STATELESS_PROTOCOL_VERSION: &str = "2026-07-28";
pub(super) const MCP_SUPPORTED_PROTOCOL_VERSIONS: &[&str] = &[
    MCP_STATELESS_PROTOCOL_VERSION,
    MCP_CHATGPT_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSION,
];
/// Single source of truth for the JSON-RPC methods advertised by `GET /mcp`.
/// Must match the facade router; pinned by `mcp_info_advertised_methods_match_dispatch`.
pub(super) const MCP_INFO_METHODS: &[&str] = &[
    "server/discover",
    "initialize",
    "ping",
    "tools/list",
    "tools/call",
    "resources/list",
    "resources/read",
    "notifications/initialized",
];

#[derive(Debug, Deserialize)]
pub(super) struct JsonRpcRequest {
    #[serde(default)]
    pub(super) jsonrpc: Option<String>,
    pub(super) method: String,
    #[serde(default)]
    pub(super) params: Value,
    #[serde(default)]
    pub(super) id: Option<Value>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum McpProtocolEra {
    Legacy,
    Stateless2026,
}

pub(super) fn request_protocol_version(params: &Value) -> Option<&str> {
    params
        .get("_meta")
        .and_then(|meta| meta.get("io.modelcontextprotocol/protocolVersion"))
        .and_then(Value::as_str)
}

pub(super) fn request_client_capabilities(params: &Value) -> Option<&Value> {
    params
        .get("_meta")
        .and_then(|meta| meta.get("io.modelcontextprotocol/clientCapabilities"))
}

pub(super) fn request_client_info_is_valid(params: &Value) -> bool {
    let Some(meta) = params.get("_meta").and_then(Value::as_object) else {
        return true;
    };
    let Some(client_info) = meta.get("io.modelcontextprotocol/clientInfo") else {
        return true;
    };
    let Some(client_info) = client_info.as_object() else {
        return false;
    };
    client_info.get("name").is_some_and(Value::is_string)
        && client_info.get("version").is_some_and(Value::is_string)
}

#[cfg(test)]
pub(super) fn inferred_protocol_era(request: &JsonRpcRequest) -> McpProtocolEra {
    if request_protocol_version(&request.params) == Some(MCP_STATELESS_PROTOCOL_VERSION) {
        McpProtocolEra::Stateless2026
    } else {
        McpProtocolEra::Legacy
    }
}

pub(super) fn legacy_initialize_protocol_version(params: &Value) -> &'static str {
    match params.get("protocolVersion").and_then(Value::as_str) {
        Some(MCP_CHATGPT_PROTOCOL_VERSION) => MCP_CHATGPT_PROTOCOL_VERSION,
        Some(MCP_PROTOCOL_VERSION) => MCP_PROTOCOL_VERSION,
        _ => MCP_PROTOCOL_VERSION,
    }
}

fn with_instructions(mut payload: Value, instructions: Option<&str>) -> Value {
    if let Some(instructions) = instructions {
        payload
            .as_object_mut()
            .expect("MCP discovery payload must be an object")
            .insert("instructions".to_string(), json!(instructions));
    }
    payload
}

pub(super) fn server_discover_payload(
    capabilities: Value,
    runtime_exposure_name: &str,
    instructions: Option<&str>,
) -> Value {
    with_instructions(
        json!({
            "resultType": "complete",
            "ttlMs": 0,
            "cacheScope": "private",
            "runtimeExposure": runtime_exposure_name,
            "supportedVersions": [
                MCP_STATELESS_PROTOCOL_VERSION,
                MCP_CHATGPT_PROTOCOL_VERSION,
                MCP_PROTOCOL_VERSION
            ],
            "capabilities": capabilities,
            "_meta": {
                "io.modelcontextprotocol/serverInfo": {
                    "name": "webcodex",
                    "version": env!("CARGO_PKG_VERSION")
                }
            }
        }),
        instructions,
    )
}

pub(super) fn legacy_initialize_payload(
    params: &Value,
    runtime_exposure_name: &str,
    instructions: Option<&str>,
) -> Value {
    with_instructions(
        json!({
            "protocolVersion": legacy_initialize_protocol_version(params),
            "capabilities": {
                "tools": {
                    "listChanged": false
                }
            },
            "serverInfo": {
                "name": "webcodex",
                "version": env!("CARGO_PKG_VERSION"),
                "runtimeExposure": runtime_exposure_name
            }
        }),
        instructions,
    )
}

pub(super) fn era_label(protocol_era: McpProtocolEra) -> &'static str {
    match protocol_era {
        McpProtocolEra::Legacy => "legacy",
        McpProtocolEra::Stateless2026 => "stateless_2026",
    }
}

#[cfg(test)]
mod instructions_tests {
    use super::*;

    #[test]
    fn initialize_includes_configured_instructions() {
        let payload = legacy_initialize_payload(&json!({}), "runtime", Some("verify first"));
        assert_eq!(payload["instructions"], "verify first");
    }

    #[test]
    fn initialize_omits_unconfigured_instructions() {
        let payload = legacy_initialize_payload(&json!({}), "runtime", None);
        assert!(payload.get("instructions").is_none());
    }

    #[test]
    fn stateless_discovery_includes_configured_instructions() {
        let payload =
            server_discover_payload(json!({"tools": {}}), "runtime", Some("verify first"));
        assert_eq!(payload["instructions"], "verify first");
    }
}
