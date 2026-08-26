# Shooter and Real-Time Action Combat

Read this when aiming, firing, projectiles/hitscan, melee/action chains, health/damage, weapons, cover, recoil, hit registration, aim assistance, or high-speed combat feedback are central. For online play also read [multiplayer-networking.md](multiplayer-networking.md); for AI enemies read [game-ai-and-navigation.md](game-ai-and-navigation.md).

## Make combat state authoritative

Record input/fire cadence, weapon state machine, ammo/reload/cooldown, damage/armor/status ordering, hitscan/projectile ownership, collision layers/masks, team/friendly-fire rules, spawn protection, death/respawn and pause/restart boundaries. Separate authoritative hit/damage state from provisional recoil, muzzle, trail, impact, hit marker, audio and camera presentation.

Each attack needs stable IDs/ticks and exactly-once consequences. Test press/hold/release, swap during reload/action, empty magazine/resource, interruption, simultaneous hits, overkill, invulnerability, self/friendly hit, wall/penetration/range boundary, projectile lifetime, moving target and target destruction. Online hit validation follows the network authority/rewind contract; a client hit marker is not damage truth.

## Preserve aim and readability

Mouse, stick and touch/gyro aim need separate sensitivity/dead-zone/acceleration curves. Aim assist must declare eligible targets, cone/range, occlusion, slowdown/magnetism, target switching and competitive policy. Recoil/spread should be inspectable and reset according to the authored rule rather than frame rate.

Use `assets/shooter-action-review.template.md` for quiet/normal/dense/peak combat, every supported aim modality, low-health/ammo states, target occlusion, close/long range, death/respawn and result. Review silhouette, threat direction, hit ownership, damage cause, crosshair/weapon obstruction, VFX overdraw, audio priority and whether HUD remains glanceable during action.

Human combat acceptance is blocking for a complete action game: response, aim feel, telegraph/reaction fairness, hit confirmation, camera motion, time-to-kill, recovery and difficulty cannot be certified by damage arithmetic alone.

