# Vehicles, Racing, and Physics-Driven Games

Read this when vehicle handling, racing lines, laps/checkpoints, stunts, traction, suspension, boats/aircraft, or deterministic ghosts/replays are central. Apply [input-and-accessibility.md](input-and-accessibility.md) and the relevant 2D/3D production guide.

## Define the handling contract

Record vehicle type, simulation tick, mass/center of mass, drive/brake/steering model, grip/slip or buoyancy/lift assumptions, assists, surface materials, top speed/acceleration/braking/turning budgets, airborne/flip recovery, camera modes, supported devices and target frame-rate range. Tune through project-owned Resources rather than scattered literals.

Physics feel is target-build behavior. Test identical input traces at every supported render cap while retaining the intended fixed physics rate. Record path/time/speed deviation, not only whether the vehicle reached the finish. Do not silently change physics tick to fix rendering or camera judder.

## Author and validate the course

Check spawn grid, track bounds, checkpoint order and direction, lap completion, shortcuts/cuts, reverse/wrong-way, missed checkpoint recovery, reset/respawn, pit/service states, finish ties, pause/restart and result persistence. Check visible road against collision, barriers, curbs, ramps, water/terrain transitions, tunnel/occlusion camera behavior and high-speed streaming.

Use `assets/vehicle-racing-review.template.md` for raw target-build evidence at low/high speed, collision, airborne/recovery, dense opponents, cockpit/chase cameras, full lap/result and supported devices. Vehicle art, wheel/steering animation, contact VFX, skid/wake audio and camera motion must agree with actual force/contact state.

Human handling review is blocking for a complete vehicle game. Judge response, controllability near the limit, assists, recovery, camera sickness/readability, collision fairness, opponent contact and whether keyboard/controller/steering inputs each receive appropriate curves rather than one copied sensitivity.

