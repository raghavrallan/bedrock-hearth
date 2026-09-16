# Bugs / Known Issues

- **IPv6 join** — Using the public/IPv6 address can crash or freeze the Bedrock client; use LAN IPv4 or Tailscale IPv4 (`FRIENDS.txt` / `PUBLIC.txt`).
- **Empty veinminer bind** — If `addons/veinminer` is empty/missing files, the pack fails silently; look for `Pack Stack - Friends SMP Vein Miner` in logs.
- **Wrong xray texture names** — Invalid names in `xray-blocks.txt` fail silently (block stays opaque). Build script rejects ore textures.
- **X-ray + Smooth Lighting** — With xray installed, Smooth Lighting must be off or ores can render black.
- **LAN address discovery** — Dashboard avoids some host networking probes that hung `/api/status` on this machine (see comment in `lan_addresses()`).
