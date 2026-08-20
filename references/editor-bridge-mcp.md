# Godot Editor Bridge and MCP

Read this when the task involves live editor automation, an MCP server, or a bridge between an AI client and Godot. The bridge augments the scene-first workflow; it does not replace saved `.tscn`/`.tres` source, engine validation, or visual review.

## Separate the terms

- **Bridge:** the integration layer that translates safe structured operations into Godot editor/runtime actions and returns state, logs, or captures.
- **MCP server:** a process that exposes tools/resources/prompts through the Model Context Protocol. “Server” describes its role; it does not imply a cloud machine.
- **MCP client:** Codex, Claude Code/Desktop, or another host that discovers and calls those tools.
- **Godot addon:** normally an `EditorPlugin` running inside the editor, where it can inspect the live scene tree, use editor APIs, participate in UndoRedo, and capture editor-specific state.

## Recommended topology

For local game development, prefer:

```text
Codex / Claude (MCP client)
        |
        | stdio, local child process
        v
Godot MCP bridge process
        |
        | authenticated loopback IPC
        v
Godot EditorPlugin <-> open project / running game
```

The MCP process and Godot editor normally run on the same developer machine. No public port, VPS, domain, or cloud deployment is required.

Choose Streamable HTTP only when the bridge must be a long-lived shared service, support several clients, or run beside a remote Godot/CI worker. A remote MCP server cannot directly manipulate a user's local editor unless a separate local agent/plugin connects outward or a tightly controlled tunnel is added.

## Why both a server and an addon

The MCP layer handles protocol discovery, schemas, client sessions, structured results, and authorization. The Godot addon has the editor context needed for live scene selection, open/unsaved scenes, editor UndoRedo, filesystem scan/import state, debugger messages, and viewport capture.

A command-line-only bridge can still run imports, scenes, auditors, and file edits. It cannot reliably know unsaved editor state or perform editor-native changes. Do not claim live editor control if only CLI/file access exists.

## Minimum useful tool surface

Start read-heavy and small. Return compact JSON plus artifact paths instead of entire scene files or logs.

Read-only tools:

- `project_info`: Godot version, renderer, project path, main scene, open scene, run state;
- `scene_tree`: bounded tree with stable node paths, types, owners, scripts, and instance sources;
- `inspect_node`: selected properties, groups, signals, and editable resource references;
- `editor_diagnostics`: import/script/runtime errors with pagination and severity filters;
- `asset_import_state`: source/import status and settings for selected assets;
- `capture_viewport`: editor or runtime screenshot with dimensions and state label.

Mutation tools, added only after read-only operation is reliable:

- `open_scene`, `instantiate_scene`, `add_node`, `remove_node`;
- `set_property`, `assign_resource`, `connect_signal`, `disconnect_signal`;
- `save_scene`, `run_scene`, `stop_running`;
- `undo`, `redo` and transaction begin/commit/cancel.

Do not expose arbitrary shell execution, unrestricted filesystem writes, arbitrary GDScript evaluation, or “set any object property by ObjectID”. Keep CLI and content-generation tools outside the editor bridge unless there is a narrow allowlisted reason.

## Safety and correctness contract

- Bind network transports to loopback by default and validate the HTTP `Host` header.
- Pin every session to one resolved project root; allow only intended `res://`/`user://` paths.
- Handshake on project path, project identity, Godot version, addon version, bridge version, and session nonce.
- Require explicit approval for deletion, project/export setting changes, plugin changes, imports with scripts, and bulk mutations.
- Route editor mutations through UndoRedo and a transaction; report dirty/saved state.
- Reject stale operations using a scene revision or fingerprint rather than editing a tree that changed since inspection.
- Serialize mutations per editor session; use timeouts and cancellation for imports/runs/captures.
- Keep protocol logs separate from stdout for stdio; stdout must contain only MCP messages.
- Redact tokens, user paths when exporting reports, and unbounded third-party/editor content.
- Save recovery copies only in a bounded project-specific location and explain cleanup.

## Token and latency design

- Offer depth, property allowlists, pagination, and `changed_since` filters.
- Give every tool a compact default response and optional artifact/report path.
- Return node summaries and fingerprints first; fetch details only for selected nodes.
- Deduplicate diagnostics and cap log/capture history.
- Put screenshots/binary artifacts in files or media responses, not base64 inside large JSON tool results unless the client requires it.
- Expose one atomic batch/transaction tool for related edits, with a bounded operation count and per-operation results.

This saves context without hiding verification. Never omit errors or truncate silently; include counts and a continuation cursor/report path.

## What is required to build it

1. A Godot 4 addon with an `EditorPlugin`, versioned request schema, UndoRedo integration, scene-tree inspection, diagnostics, viewport capture, and a loopback IPC client/server.
2. An MCP server built with an official/community SDK for Python, TypeScript, C#, Rust, or another supported runtime.
3. A local transport. `stdio` is the simplest for one client; authenticated loopback WebSocket/TCP/HTTP can connect the MCP process to the Godot addon.
4. Client configuration for Codex/Claude and an explicit project-root argument or environment variable.
5. Contract tests for initialization, tool schemas, stale revision rejection, undo/redo, unsaved scenes, import errors, editor restart, timeouts, and malicious paths.
6. Compatibility testing for the supported Godot versions and operating systems.

## Client connection examples

Once an actual bridge entry point exists, a local Codex registration has this shape:

```powershell
codex mcp add godot-bridge -- python C:\path\to\godot_mcp_server.py --project C:\path\to\game
```

Codex also accepts a Streamable HTTP server:

```powershell
codex mcp add godot-bridge --url http://127.0.0.1:PORT/mcp
```

Claude Code local stdio registration has the same process model:

```powershell
claude mcp add godot-bridge -- python C:\path\to\godot_mcp_server.py --project C:\path\to\game
```

These commands are configuration shapes, not runnable commands until the referenced bridge implementation exists. Do not install or register a bridge silently; inspect its source and permissions first.

## Acceptance gate

Before describing the bridge as usable, prove:

- client initialization and tool discovery;
- correct project/editor identity and reconnect behavior;
- read-only inspection of a saved and an unsaved scene;
- an atomic add/set/connect/save operation followed by undo and redo;
- rejection of paths outside the project and stale revisions;
- import error and runtime error retrieval;
- editor and runtime capture;
- bounded responses and no secrets/protocol corruption in logs.

Until then, call it a bridge design or prototype, not editor integration.

Official references: [OpenAI Codex MCP](https://developers.openai.com/codex/mcp/), [MCP transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports), and [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp).
