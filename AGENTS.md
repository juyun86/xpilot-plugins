# Xpilot plugin development instructions

Read the canonical [Xpilot highest development policy](https://github.com/juyun86/xpilot/blob/xpilot/DEVELOPMENT_RULES.md) before changing this repository. With sibling checkouts, read `../xpilot/DEVELOPMENT_RULES.md` locally; use its actual path if the host checkout is elsewhere. Do not maintain a divergent copy here.

That policy is the highest project development policy and governs older README, CONTRIBUTING and API wording. It does not override user instructions, platform requirements or OS permissions. Then read this repository's CONTRIBUTING.md and README.md, and the host XPILOT.md/API sections needed by the task.

- User repository: `juyun86/xpilot-plugins`, branch `main`. Companion host: `juyun86/xpilot`, branch `xpilot`. `onemiless` is upstream, not the user's push destination.
- Check branch, HEAD, remotes and dirty files before editing. Do not create another branch/worktree unless explicitly requested, or overwrite unrelated changes.
- Plugin code, tests, resources, dist and index belong here. Generic host APIs, permission enforcement, UI framework and system checks belong in the host repository; publish required host support first.
- Do not weaken rules to fit an implementation. New claims are not OS permissions. Network/privileged operations require a documented host contract; tiles consume declared messages, not private status files.
- Prefix new parameters with `Ext`; use ParamsView. Keep logic separate from I/O. Preserve plugin.py <=150 lines, other production Python files <=400 lines, and pyray imports only in ui.py.
- Published plugin changes require a version bump and official archive/index rebuild. Binary plugins require platform and build reproduction instructions/script. Do not rewrite published versions silently.
- List failure cases before implementation, prefer repeatable E2E, and do not add after-the-fact implementation-mirroring unit tests. Run checks relevant to the changed scope and the required final release checks; documentation-only changes do not require hardware tests.
- Commit each coherent change separately. Push/deploy only within user authorization, without asking again when authorization already exists. Report local/remote/device commits separately; disclose missing checks and actual CI state.
- Historical Starlink/language findings are recorded in section 8 of the canonical policy; dated implementation results and remaining validation boundaries are in section 9. Verify the current source and evidence before reopening or marking an item complete. Adding policy or passing unrelated checks is not a fix. Do not change the device while only editing this policy.
