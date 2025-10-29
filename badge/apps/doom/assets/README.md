# Doom Badge App

A simplified doom-style raycasting game inspired by PyDoom (https://github.com/Pink-Silver/PyDoom).

## Controls

- **UP**: Move forward
- **DOWN**: Move backward  
- **A**: Turn left
- **C**: Turn right
- **B**: Shoot
- **HOME**: Return to menu

## Features

- Real-time raycasting for pseudo-3D perspective
- Distance-based wall shading
- Enemy sprites with hit detection
- Weapon system with shooting mechanics
- Muzzle flash effects
- Minimap overlay showing player position, direction, and enemies
- Simple maze navigation

## Technical Details

This implementation uses a simplified raycasting algorithm suitable for the badge's MicroPython environment. The original PyDoom is a full Python port of DOOM requiring SDL2 and OpenGL, which isn't feasible on the badge hardware. Instead, this version provides a similar gameplay experience with:

- 160x120 resolution rendering
- 160 rays cast per frame (full screen width)
- Optimized stepping algorithm for fast rendering
- Grid-based collision detection
- Perspective-correct wall and enemy rendering
- Z-sorted sprite rendering for proper depth

## Map Format

The game map is defined as a 2D array where:
- `1` = wall
- `0` = empty space

You can modify the `GAME_MAP` in `__init__.py` to create your own levels!

## Enemies

Enemies are defined in the `enemies` list as `[x, y, alive]`. You can:
- Add more enemies at different positions
- Modify enemy positions
- Adjust the enemy radius for hit detection (currently 0.3 units)
