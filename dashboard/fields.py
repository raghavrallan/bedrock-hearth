"""Every Bedrock Dedicated Server 1.26 / itzg property we can set."""

from __future__ import annotations

# kind: text | number | float | bool | select
# prop: key in server.properties

FIELDS = [
    # World & gameplay
    {"key": "SERVER_NAME", "prop": "server-name", "group": "World & gameplay", "label": "Server name", "kind": "text", "default": "Friends SMP", "help": "Name in the in-game server list. No semicolons."},
    {"key": "LEVEL_NAME", "prop": "level-name", "group": "World & gameplay", "label": "World folder name", "kind": "text", "default": "Bedrock level", "help": "Names the world folder. Changing this loads a different/new world."},
    {"key": "LEVEL_SEED", "prop": "level-seed", "group": "World & gameplay", "label": "World seed", "kind": "text", "default": "", "help": "Only used when a new world is created. Empty = random."},
    {"key": "LEVEL_TYPE", "prop": "level-type", "group": "World & gameplay", "label": "Level type", "kind": "select", "default": "DEFAULT", "options": ["DEFAULT", "FLAT", "LEGACY"], "help": "Only used when creating a new world."},
    {"key": "GAMEMODE", "prop": "gamemode", "group": "World & gameplay", "label": "Game mode", "kind": "select", "default": "survival", "options": ["survival", "creative", "adventure"]},
    {"key": "FORCE_GAMEMODE", "prop": "force-gamemode", "group": "World & gameplay", "label": "Force game mode", "kind": "bool", "default": "false", "help": "If on, everyone is forced into the mode above."},
    {"key": "DIFFICULTY", "prop": "difficulty", "group": "World & gameplay", "label": "Difficulty", "kind": "select", "default": "easy", "options": ["peaceful", "easy", "normal", "hard"]},
    {"key": "ALLOW_CHEATS", "prop": "allow-cheats", "group": "World & gameplay", "label": "Allow cheats / commands", "kind": "bool", "default": "false", "help": "Needed for /give, /tp, /gamemode. Off = even ops cannot use commands."},
    {"key": "TEXTUREPACK_REQUIRED", "prop": "texturepack-required", "group": "World & gameplay", "label": "Require texture packs", "kind": "bool", "default": "false"},
    {"key": "DEFAULT_PLAYER_PERMISSION_LEVEL", "prop": "default-player-permission-level", "group": "World & gameplay", "label": "New player permission", "kind": "select", "default": "member", "options": ["visitor", "member", "operator"]},
    {"key": "OP_PERMISSION_LEVEL", "prop": "op-permission-level", "group": "World & gameplay", "label": "Operator permission level", "kind": "number", "default": "4", "min": 1, "max": 4},

    # Players & access
    {"key": "MAX_PLAYERS", "prop": "max-players", "group": "Players & access", "label": "Max players", "kind": "number", "default": "10", "min": 1, "max": 100},
    {"key": "ONLINE_MODE", "prop": "online-mode", "group": "Players & access", "label": "Xbox Live login required", "kind": "bool", "default": "true"},
    {"key": "ALLOW_LIST", "prop": "allow-list", "group": "Players & access", "label": "Allow list (invite only)", "kind": "bool", "default": "false"},
    {"key": "WHITE_LIST", "prop": "white-list", "group": "Players & access", "label": "White list (old name)", "kind": "bool", "default": "false", "help": "Kept in sync with allow list."},
    {"key": "MSA_GAMERTAGS_ONLY", "prop": "msa-gamertags-only", "group": "Players & access", "label": "Microsoft gamertags only", "kind": "bool", "default": "false"},
    {"key": "PLAYER_IDLE_TIMEOUT", "prop": "player-idle-timeout", "group": "Players & access", "label": "Idle kick (minutes)", "kind": "number", "default": "30", "min": 0, "max": 1440, "help": "0 = never kick idle players."},
    {"key": "CHAT_RESTRICTION", "prop": "chat-restriction", "group": "Players & access", "label": "Chat restriction", "kind": "select", "default": "None", "options": ["None", "Dropped", "Disabled"]},
    {"key": "DISABLE_PLAYER_INTERACTION", "prop": "disable-player-interaction", "group": "Players & access", "label": "Disable player interaction", "kind": "bool", "default": "false"},
    {"key": "DISABLE_CUSTOM_SKINS", "prop": "disable-custom-skins", "group": "Players & access", "label": "Disable custom skins", "kind": "bool", "default": "false"},
    {"key": "DISABLE_PERSONA", "prop": "disable-persona", "group": "Players & access", "label": "Disable persona skins", "kind": "bool", "default": "false"},
    {"key": "ALLOW_PLAYER_JOINING", "prop": "allow-player-joining", "group": "Players & access", "label": "Allow player joining", "kind": "bool", "default": "true", "help": "If off, only scripts can let people in."},

    # Performance
    {"key": "VIEW_DISTANCE", "prop": "view-distance", "group": "Performance", "label": "View distance (chunks)", "kind": "number", "default": "12", "min": 5, "max": 96},
    {"key": "TICK_DISTANCE", "prop": "tick-distance", "group": "Performance", "label": "Tick / simulation distance", "kind": "number", "default": "4", "min": 4, "max": 12},
    {"key": "MAX_THREADS", "prop": "max-threads", "group": "Performance", "label": "Max threads", "kind": "number", "default": "8", "min": 0, "max": 64, "help": "0 = use as many as possible."},
    {"key": "CLIENT_SIDE_CHUNK_GENERATION_ENABLED", "prop": "client-side-chunk-generation-enabled", "group": "Performance", "label": "Client-side chunk generation", "kind": "bool", "default": "true"},
    {"key": "SERVER_BUILD_RADIUS_RATIO", "prop": "server-build-radius-ratio", "group": "Performance", "label": "Server build radius ratio", "kind": "text", "default": "Disabled", "help": "Disabled, or a number from 0.0 to 1.0."},
    {"key": "BLOCK_NETWORK_IDS_ARE_HASHES", "prop": "block-network-ids-are-hashes", "group": "Performance", "label": "Hashed block network IDs", "kind": "bool", "default": "true"},
    {"key": "DISABLE_CLIENT_VIBRANT_VISUALS", "prop": "disable-client-vibrant-visuals", "group": "Performance", "label": "Disable Vibrant Visuals on clients", "kind": "bool", "default": "true"},

    # Network
    {"key": "SERVER_PORT", "prop": "server-port", "group": "Network", "label": "IPv4 port", "kind": "number", "default": "19132", "min": 1024, "max": 65535, "help": "Also updates Docker port publish. Friends must use this port."},
    {"key": "SERVER_PORT_V6", "prop": "server-portv6", "group": "Network", "label": "IPv6 port", "kind": "number", "default": "19132", "min": 1024, "max": 65535, "help": "Kept equal to IPv4 here so both work on one port."},
    {"key": "ENABLE_LAN_VISIBILITY", "prop": "enable-lan-visibility", "group": "Network", "label": "LAN discovery", "kind": "bool", "default": "true"},
    {"key": "COMPRESSION_THRESHOLD", "prop": "compression-threshold", "group": "Network", "label": "Compression threshold", "kind": "number", "default": "1", "min": 0, "max": 65535},
    {"key": "COMPRESSION_ALGORITHM", "prop": "compression-algorithm", "group": "Network", "label": "Compression algorithm", "kind": "select", "default": "zlib", "options": ["zlib", "snappy"]},
    {"key": "TRANSPORT", "prop": "transport", "group": "Network", "label": "Transport", "kind": "select", "default": "raknet", "options": ["raknet", "nethernet"], "help": "Keep raknet unless you know you need NetherNet."},
    {"key": "ENABLE_PACKET_RATE_LIMITER", "prop": "enable-packet-rate-limiter", "group": "Network", "label": "Packet rate limiter", "kind": "bool", "default": "false"},
    {"key": "SERVER_IP", "prop": "server-ip", "group": "Network", "label": "Bind IP", "kind": "text", "default": "", "help": "Empty binds all interfaces. Only used with nethernet transport."},
    {"key": "SERVER_UDP_PORTS", "prop": "server-udp-ports", "group": "Network", "label": "UDP port mapping", "kind": "text", "default": "", "help": "Only used with nethernet. Example: 19132:32000"},

    # Anti-cheat / movement
    {"key": "SERVER_AUTHORITATIVE_MOVEMENT_STRICT", "prop": "server-authoritative-movement-strict", "group": "Anti-cheat & movement", "label": "Strict movement", "kind": "bool", "default": "false"},
    {"key": "SERVER_AUTHORITATIVE_DISMOUNT_STRICT", "prop": "server-authoritative-dismount-strict", "group": "Anti-cheat & movement", "label": "Strict dismount", "kind": "bool", "default": "false"},
    {"key": "SERVER_AUTHORITATIVE_ENTITY_INTERACTIONS_STRICT", "prop": "server-authoritative-entity-interactions-strict", "group": "Anti-cheat & movement", "label": "Strict entity interactions", "kind": "bool", "default": "false"},
    {"key": "PLAYER_POSITION_ACCEPTANCE_THRESHOLD", "prop": "player-position-acceptance-threshold", "group": "Anti-cheat & movement", "label": "Position acceptance threshold", "kind": "float", "default": "0.5", "min": 0.0, "max": 5.0},
    {"key": "PLAYER_MOVEMENT_ACTION_DIRECTION_THRESHOLD", "prop": "player-movement-action-direction-threshold", "group": "Anti-cheat & movement", "label": "Attack direction threshold", "kind": "float", "default": "0.85", "min": -1.0, "max": 1.0},
    {"key": "SERVER_AUTHORITATIVE_BLOCK_BREAKING", "prop": "server-authoritative-block-breaking", "group": "Anti-cheat & movement", "label": "Server-authoritative block breaking", "kind": "bool", "default": "false"},
    {"key": "SERVER_AUTHORITATIVE_BLOCK_BREAKING_PICK_RANGE_SCALAR", "prop": "server-authoritative-block-breaking-pick-range-scalar", "group": "Anti-cheat & movement", "label": "Block-break range scalar", "kind": "float", "default": "1.5", "min": 1.0, "max": 10.0},
    {"key": "PLAYER_MOVEMENT_SCORE_THRESHOLD", "prop": "player-movement-score-threshold", "group": "Anti-cheat & movement", "label": "Movement score threshold (legacy)", "kind": "number", "default": "20", "min": 0, "max": 1000},
    {"key": "PLAYER_MOVEMENT_DISTANCE_THRESHOLD", "prop": "player-movement-distance-threshold", "group": "Anti-cheat & movement", "label": "Movement distance threshold (legacy)", "kind": "float", "default": "0.3", "min": 0.0, "max": 10.0},
    {"key": "PLAYER_MOVEMENT_DURATION_THRESHOLD_IN_MS", "prop": "player-movement-duration-threshold-in-ms", "group": "Anti-cheat & movement", "label": "Movement duration threshold ms (legacy)", "kind": "number", "default": "500", "min": 0, "max": 10000},
    {"key": "CORRECT_PLAYER_MOVEMENT", "prop": "correct-player-movement", "group": "Anti-cheat & movement", "label": "Correct player movement (legacy)", "kind": "bool", "default": "false"},
    {"key": "SERVER_AUTHORITATIVE_MOVEMENT", "prop": "server-authoritative-movement", "group": "Anti-cheat & movement", "label": "Authoritative movement (legacy)", "kind": "select", "default": "server-auth", "options": ["client-auth", "server-auth", "server-auth-with-rewind"]},

    # Logging
    {"key": "CONTENT_LOG_FILE_ENABLED", "prop": "content-log-file-enabled", "group": "Logging & extras", "label": "Content log file", "kind": "bool", "default": "false"},
    {"key": "CONTENT_LOG_CONSOLE_OUTPUT_ENABLED", "prop": "content-log-console-output-enabled", "group": "Logging & extras", "label": "Content log to console", "kind": "bool", "default": "false"},
    {"key": "CONTENT_LOG_LEVEL", "prop": "content-log-level", "group": "Logging & extras", "label": "Content log level", "kind": "select", "default": "info", "options": ["error", "warning", "info", "verbose"]},
    {"key": "ITEM_TRANSACTION_LOGGING_ENABLED", "prop": "item-transaction-logging-enabled", "group": "Logging & extras", "label": "Item transaction logging", "kind": "bool", "default": "false"},
    {"key": "EMIT_SERVER_TELEMETRY", "prop": "emit-server-telemetry", "group": "Logging & extras", "label": "Emit server telemetry", "kind": "bool", "default": "false"},
    {"key": "VARIABLES", "prop": "variables", "group": "Logging & extras", "label": "Custom variables", "kind": "text", "default": "", "help": "Optional itzg VARIABLES string."},

    # Script debugger
    {"key": "ALLOW_OUTBOUND_SCRIPT_DEBUGGING", "prop": "allow-outbound-script-debugging", "group": "Script debugger", "label": "Allow outbound script debugging", "kind": "bool", "default": "false"},
    {"key": "ALLOW_INBOUND_SCRIPT_DEBUGGING", "prop": "allow-inbound-script-debugging", "group": "Script debugger", "label": "Allow inbound script debugging", "kind": "bool", "default": "false"},
    {"key": "FORCE_INBOUND_DEBUG_PORT", "prop": "force-inbound-debug-port", "group": "Script debugger", "label": "Inbound debug port", "kind": "number", "default": "19144", "min": 1, "max": 65535},
    {"key": "SCRIPT_DEBUGGER_AUTO_ATTACH", "prop": "script-debugger-auto-attach", "group": "Script debugger", "label": "Debugger auto-attach", "kind": "select", "default": "disabled", "options": ["disabled", "connect", "listen"]},
    {"key": "SCRIPT_DEBUGGER_AUTO_ATTACH_CONNECT_ADDRESS", "prop": "script-debugger-auto-attach-connect-address", "group": "Script debugger", "label": "Debugger connect address", "kind": "text", "default": "localhost:19144"},
    {"key": "SCRIPT_DEBUGGER_AUTO_ATTACH_TIMEOUT", "prop": "script-debugger-auto-attach-timeout", "group": "Script debugger", "label": "Debugger attach timeout (sec)", "kind": "number", "default": "0", "min": 0, "max": 300},
    {"key": "SCRIPT_DEBUGGER_PASSCODE", "prop": "script-debugger-passcode", "group": "Script debugger", "label": "Debugger passcode", "kind": "text", "default": ""},

    # Script watchdog
    {"key": "SCRIPT_WATCHDOG_ENABLE", "prop": "script-watchdog-enable", "group": "Script watchdog", "label": "Enable script watchdog", "kind": "bool", "default": "true"},
    {"key": "SCRIPT_WATCHDOG_ENABLE_EXCEPTION_HANDLING", "prop": "script-watchdog-enable-exception-handling", "group": "Script watchdog", "label": "Watchdog exception handling", "kind": "bool", "default": "true"},
    {"key": "SCRIPT_WATCHDOG_ENABLE_SHUTDOWN", "prop": "script-watchdog-enable-shutdown", "group": "Script watchdog", "label": "Watchdog can shut down server", "kind": "bool", "default": "true"},
    {"key": "SCRIPT_WATCHDOG_HANG_EXCEPTION", "prop": "script-watchdog-hang-exception", "group": "Script watchdog", "label": "Hang throws exception", "kind": "bool", "default": "true"},
    {"key": "SCRIPT_WATCHDOG_HANG_THRESHOLD", "prop": "script-watchdog-hang-threshold", "group": "Script watchdog", "label": "Hang threshold (ms)", "kind": "number", "default": "10000", "min": 1, "max": 120000},
    {"key": "SCRIPT_WATCHDOG_SPIKE_THRESHOLD", "prop": "script-watchdog-spike-threshold", "group": "Script watchdog", "label": "Spike threshold", "kind": "number", "default": "100", "min": 0, "max": 10000},
    {"key": "SCRIPT_WATCHDOG_SLOW_THRESHOLD", "prop": "script-watchdog-slow-threshold", "group": "Script watchdog", "label": "Slow script threshold", "kind": "number", "default": "10", "min": 0, "max": 10000},
    {"key": "SCRIPT_WATCHDOG_MEMORY_WARNING", "prop": "script-watchdog-memory-warning", "group": "Script watchdog", "label": "Script memory warning (MB)", "kind": "number", "default": "100", "min": 0, "max": 2000},
    {"key": "SCRIPT_WATCHDOG_MEMORY_LIMIT", "prop": "script-watchdog-memory-limit", "group": "Script watchdog", "label": "Script memory limit (MB)", "kind": "number", "default": "250", "min": 0, "max": 2000},

    # Diagnostics
    {"key": "DIAGNOSTICS_CAPTURE_AUTO_START", "prop": "diagnostics-capture-auto-start", "group": "Diagnostics", "label": "Auto-start diagnostics capture", "kind": "bool", "default": "false"},
    {"key": "DIAGNOSTICS_CAPTURE_MAX_FILES", "prop": "diagnostics-capture-max-files", "group": "Diagnostics", "label": "Diagnostics max files", "kind": "number", "default": "5", "min": 0, "max": 50},
    {"key": "DIAGNOSTICS_CAPTURE_MAX_FILE_SIZE", "prop": "diagnostics-capture-max-file-size", "group": "Diagnostics", "label": "Diagnostics max file size (bytes)", "kind": "number", "default": "2097152", "min": 1024, "max": 104857600},
    {"key": "SENTRY_RATE_LIMIT_WINDOW", "prop": "sentry-rate-limit-window", "group": "Diagnostics", "label": "Sentry rate-limit window (sec)", "kind": "number", "default": "60", "min": 0, "max": 3600},
    {"key": "SENTRY_MAX_EVENTS_PER_WINDOW", "prop": "sentry-max-events-per-window", "group": "Diagnostics", "label": "Sentry max events per window", "kind": "number", "default": "10", "min": 0, "max": 1000},
    {"key": "ENABLE_PROFILER", "prop": "enable-profiler", "group": "Diagnostics", "label": "Enable profiler", "kind": "bool", "default": "false"},
    {"key": "ENABLE_EDITOR_NETWORK_METRICS", "prop": "enable-editor-network-metrics", "group": "Diagnostics", "label": "Editor network metrics", "kind": "bool", "default": "false"},
    {"key": "CONVERT_WORLD_TO_EDITOR_PROJECT", "prop": "convert-world-to-editor-project", "group": "Diagnostics", "label": "Convert world to Editor project", "kind": "bool", "default": "false", "help": "Only matters if the server is launched with Editor=true."},
]

GROUPS = []
for field in FIELDS:
    if field["group"] not in GROUPS:
        GROUPS.append(field["group"])

BY_KEY = {f["key"]: f for f in FIELDS}
KEYS = [f["key"] for f in FIELDS]
