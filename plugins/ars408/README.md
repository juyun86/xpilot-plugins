# ARS408 Radar Receiver

Migration order confirmed by the owner: radar was installed first; overtaking
was added later. Complete the radar integration independently before resuming
navigation/overtaking work. Neither feature is a prerequisite for this driver.

An independent `source:radar` plugin extracted from the user's working C3XL
commit `6db98169cfefd6e7e4bd1f3bdaaf70623f79750d`. No navigation imports, route
decisions, lane changes or overtaking policy live here. The DBC is bundled and
loaded by absolute package path, without changing opendbc or global DBC paths.

The receiver preserves sensor decode, upside-down coordinate conversion,
quality states, exact/partial cycle assembly, track association/grace, duplicate
suppression, truck-echo handling and diagnostics. It returns standard RadarData
through the existing host radar_interface hook. Enabling an external receiver
does not modify factory CP/CP_SP flags or the original fallback receiver.

## Important installation boundary

This version is a **receiver**, not a complete replacement for the old C3XL
hardware integration. It transmits no CAN and changes no radar configuration.
It requires the installation to provide radar motion inputs already. Missing
motion input remains a sensor fault; it is not replaced by zero yaw/speed.
The calibrated deviceMotion input is connected through the host card_context
API, but Panda TX integration remains inactive. Do not uninstall the old working
system on the strength of decoder/regression tests.

`transmitter.py` retains the reviewed pure configuration/filter/motion encoders
and their tests for the subsequent execution-port migration. Merely having an
encoder does not authorize transmission: the plugin declares no can.tx claims
and has no observe_can/control_sends override. No firmware change or flash is
performed. Hardware configuration and motion TX need their own declared host
and Panda contracts before they can be enabled.

`motion.py` now also preserves the old calibrated `deviceMotion` extraction,
including 150 ms motion freshness, 2 s calibration freshness, sensor health,
finite values, calibrated axis transformation, and cache invalidation. The
plugin's `card_context` hook consumes the host's declared `deviceMotion` and
`extrinsicsCalibration` readers, injects its PoseCalibrator, and updates its
motion encoder. It invalidates the old sample before processing each context.
The helper does not subscribe or send frames.
The sender must receive this valid calibrated sample, never substitute zero or
Tesla CarState.yawRate. The sender and receiver share the same freshness constant.

Remaining execution port: connect the motion encoder to the authorized send
hook at 20 Hz, and authorize exact bus-1 `0x300`/`0x301` two-byte messages in the host/Panda
contract. Existing `template_clone.v1` requires equal RX/TX lengths and a fresh
RX template: the radar's eight-byte `0x201` or four-byte `0x60A` frames cannot
be declared as a two-byte template. Do not fabricate a template or relax the
global rules. Configuration/query encoders likewise remain inactive.

Enable only while parked, with the correct source and motion provisioning, then
restart. CAN bus is 1, sensor ID 0, expected object output/quality and 250 m max
distance follow the source baseline. Mount inversion defaults true to preserve
this user's confirmed old installation; set it to match the actual installation,
never infer orientation from radar model. Settings are read at drive startup.

Only one source:radar provider wins. Other radar models get independent packages;
this plugin makes no compatibility claim for them. Radar errors and unknown or
unmeasured targets must not be taken as proof that adjacent lanes are clear.
The existing host falls back to its original receiver on exceptions; consumers
cannot infer the current source/coverage from the selected manifest alone.

## Provenance and validation

`source.json` lists exact source hashes and narrowly scoped port changes.
Existing decoder/cycle/diagnostic/tracker/truck-echo/interface/encoder tests were
ported before implementation; test fixture imports and DBC lookup are local.
The receiver, tracker and filter algorithms were not rewritten. The source's
old CP flag in the encoder constructor is retained only as legacy compatibility;
new callers can explicitly provide enabled=True/False. No navigation consumer
is allowed to use that model flag as its radar health test.

Tests validate code and synthetic frames. Actual new-plugin vehicle use and
full old-system feature equivalence require later integration acceptance.
