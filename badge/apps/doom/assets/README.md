# Doom Badge App

A simplified doom-style raycasting game inspired by PyDoom (https://github.com/Pink-Silver/PyDoom).

## Controls

- **UP**: Move forward
- **DOWN**: Move backward  
- **A**: Turn left
- **C**: Turn right
- **HOME**: Return to menu

## Features

- Real-time raycasting for pseudo-3D perspective
- Distance-based wall shading
- Minimap overlay showing player position and direction
- Simple maze navigation

## Technical Details

This implementation uses a simplified raycasting algorithm suitable for the badge's MicroPython environment. The original PyDoom is a full Python port of DOOM requiring SDL2 and OpenGL, which isn't feasible on the badge hardware. Instead, this version provides a similar gameplay experience with:

- 160x120 resolution rendering
- 80 rays cast per frame for performance
- Grid-based collision detection
- Perspective-correct wall rendering

## Map Format

The game map is defined as a 2D array where:
- `1` = wall
- `0` = empty space

You can modify the `GAME_MAP` in `__init__.py` to create your own levels!
