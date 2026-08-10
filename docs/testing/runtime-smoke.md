# Runtime smoke testing

The repository has two disposable Minecraft 26.2 runtime paths:

- `main` starts a Fabric server with the built mod JAR.
- `lite` starts a vanilla server with the built clean-tabs datapack ZIP in a
  generated world's `datapacks` directory.

Both paths run `tools/runtime_smoke.py` through local RCON. The smoke check
verifies that Matcha is enabled, the load function creates `sleepTimerScore`,
`keepInventory` is enabled, `/reload` preserves the objective, the scoreboard
setup function can recreate the objective, and the server log contains no
Matcha-owned data/function load errors.

The smoke test is intentionally disposable and server-side. It does not
replace the manual checks that require a real player, including two-player
sleep quorum, fishing outcomes, custom-model presentation, or Warding Stone
placement inside a generated Trial Chamber.

For the 5IVE client, validate both Matcha load errors and GPU routing from the
fresh launch log:

```powershell
python tools/runtime_smoke.py --log "$env:APPDATA\ModrinthApp\profiles\5IVE\logs\latest.log" --log-only --require-gpu "NVIDIA GeForce RTX 5080"
```

The GPU assertion is opt-in because dedicated-server logs do not create a
graphics device.

## CI behavior

- Pushes and pull requests targeting `main` run the Fabric path.
- Pushes and pull requests targeting `lite` run the vanilla datapack path.
- The generated server, world, RCON settings, and logs live only in the CI
  workspace and are uploaded as diagnostics if the job fails.

## Local smoke run

Use Java 25, `curl`, and `jq` to mirror the Lite job:

1. Build the Lite archives with `python tools/build_distribution.py`.
2. Download the Minecraft 26.2 dedicated server from Mojang's version
   manifest.
3. Create a disposable server directory and copy the clean-tabs datapack ZIP
   into its `world/datapacks` directory.
4. Start the server with RCON enabled.
5. Run:

   ```powershell
   python tools/runtime_smoke.py --log .runtime-lite-server/server.log --port 25576 --password matcha-runtime-smoke
   ```

Delete the disposable server directory after the run. Never point this test
at a real world.
