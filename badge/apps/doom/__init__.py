import sys
import os
import math

from badgeware import screen, PixelFont, shapes, brushes, io, run

# Screen dimensions
WIDTH = 160
HEIGHT = 120

# Game map - 1 is wall, 0 is empty
GAME_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_WIDTH = len(GAME_MAP[0])
MAP_HEIGHT = len(GAME_MAP)

# Player state
player_x = 2.5
player_y = 2.5
player_angle = 0.0

# Movement speed
MOVE_SPEED = 0.08
ROTATE_SPEED = 0.12

# Enemy data - [x, y, alive]
enemies = [
    [7.5, 2.5, True],
    [5.5, 5.5, True],
    [7.5, 7.5, True],
]

# Weapon state
weapon_cooldown = 0
muzzle_flash = 0

# Raycasting settings
FOV = 60  # Field of view in degrees
NUM_RAYS = 160  # Number of rays to cast (full screen width)
MAX_DEPTH = 10.0

# Colors
FLOOR_COLOR = (50, 50, 50)
CEILING_COLOR = (30, 30, 50)
WALL_COLOR_DARK = (100, 100, 100)
WALL_COLOR_LIGHT = (150, 150, 150)
SKY_COLOR = (20, 20, 40)

# Load font
small_font = PixelFont.load("/system/assets/fonts/nope.ppf")


def init():
    """Initialize the game"""
    screen.font = small_font


def cast_ray(angle):
    """Cast a single ray and return distance to wall and any enemy hit"""
    global player_x, player_y
    
    # Ray direction
    ray_x = math.cos(angle)
    ray_y = math.sin(angle)
    
    # Start from player position
    x = player_x
    y = player_y
    
    # Optimized stepping - use larger steps
    step_size = 0.05
    max_steps = int(MAX_DEPTH / step_size)
    
    # Pre-calculate enemy intersections using ray-circle intersection
    closest_enemy = None
    closest_enemy_dist = MAX_DEPTH
    closest_enemy_dist_sq = MAX_DEPTH * MAX_DEPTH
    enemy_radius = 0.3
    enemy_radius_sq = enemy_radius * enemy_radius
    
    for i, enemy in enumerate(enemies):
        if enemy[2]:  # If alive
            ex, ey = enemy[0], enemy[1]
            
            # Vector from player to enemy
            dx = ex - player_x
            dy = ey - player_y
            
            # Project enemy position onto ray direction
            dot = dx * ray_x + dy * ray_y
            
            # If enemy is behind the player (in opposite direction of ray), skip it
            if dot < 0:
                continue
            
            # Find closest point on ray to enemy center
            closest_x = player_x + ray_x * dot
            closest_y = player_y + ray_y * dot
            
            # Squared distance from enemy center to closest point on ray (avoid sqrt)
            dist_to_ray_sq = (ex - closest_x) ** 2 + (ey - closest_y) ** 2
            
            # Check if ray passes through enemy's radius
            if dist_to_ray_sq < enemy_radius_sq:
                # Calculate actual Euclidean distance for correct enemy ordering
                enemy_dist_sq = dx * dx + dy * dy
                if enemy_dist_sq < closest_enemy_dist_sq:
                    closest_enemy = i
                    closest_enemy_dist_sq = enemy_dist_sq
                    closest_enemy_dist = math.sqrt(enemy_dist_sq)
    
    # Step along ray to find walls
    for step in range(max_steps):
        x += ray_x * step_size
        y += ray_y * step_size
        
        # Check map boundaries
        map_x = int(x)
        map_y = int(y)
        
        if map_x < 0 or map_x >= MAP_WIDTH or map_y < 0 or map_y >= MAP_HEIGHT:
            return MAX_DEPTH, False, closest_enemy, closest_enemy_dist
        
        # Check if ray hit a wall
        if GAME_MAP[map_y][map_x] == 1:
            distance = math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)
            # Determine if we hit vertical or horizontal wall for shading
            frac_x = x - map_x
            frac_y = y - map_y
            is_vertical = abs(frac_x) < 0.1 or abs(frac_x - 1) < 0.1
            return distance, is_vertical, closest_enemy, closest_enemy_dist
    
    return MAX_DEPTH, False, closest_enemy, closest_enemy_dist


def render_3d_view():
    """Render the 3D raycasted view"""
    global player_angle, muzzle_flash
    
    # Draw ceiling
    screen.brush = brushes.color(*CEILING_COLOR)
    screen.draw(shapes.rectangle(0, 0, WIDTH, HEIGHT // 2))
    
    # Draw floor
    screen.brush = brushes.color(*FLOOR_COLOR)
    screen.draw(shapes.rectangle(0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    
    # Store enemy rendering info for z-sorting
    enemy_render_data = []
    
    # Cast rays for 3D view
    ray_angle_step = math.radians(FOV) / NUM_RAYS
    start_angle = player_angle - math.radians(FOV / 2)
    
    for i in range(NUM_RAYS):
        ray_angle = start_angle + i * ray_angle_step
        distance, is_vertical, enemy_idx, enemy_dist = cast_ray(ray_angle)
        
        # Store enemy data for rendering after walls
        if enemy_idx is not None and enemy_dist < distance:
            enemy_render_data.append((i, enemy_dist, ray_angle))
        
        # Fix fish-eye effect
        distance *= math.cos(ray_angle - player_angle)
        
        # Calculate wall height based on distance
        if distance > 0:
            wall_height = min((HEIGHT * 0.6) / distance, HEIGHT)
        else:
            wall_height = HEIGHT
        
        # Calculate wall position
        wall_top = (HEIGHT - wall_height) // 2
        wall_bottom = wall_top + wall_height
        
        # Choose wall color based on orientation
        if is_vertical:
            color = WALL_COLOR_LIGHT
        else:
            color = WALL_COLOR_DARK
        
        # Darken based on distance
        brightness = max(0.3, 1.0 - (distance / MAX_DEPTH) * 0.7)
        color = (int(color[0] * brightness), int(color[1] * brightness), int(color[2] * brightness))
        
        # Draw wall slice (1 pixel wide for full screen)
        x = i
        
        screen.brush = brushes.color(*color)
        screen.draw(shapes.rectangle(x, int(wall_top), 1, int(wall_height)))
    
    # Render enemies
    for ray_idx, enemy_dist, ray_angle in enemy_render_data:
        # Fix fish-eye effect for enemy
        enemy_dist *= math.cos(ray_angle - player_angle)
        
        if enemy_dist > 0:
            enemy_height = min((HEIGHT * 0.4) / enemy_dist, HEIGHT * 0.6)
            enemy_top = (HEIGHT - enemy_height) // 2
            
            # Red color for enemies, darker with distance
            brightness = max(0.3, 1.0 - (enemy_dist / MAX_DEPTH) * 0.7)
            enemy_color = (int(200 * brightness), int(50 * brightness), int(50 * brightness))
            
            screen.brush = brushes.color(*enemy_color)
            screen.draw(shapes.rectangle(ray_idx, int(enemy_top), 1, int(enemy_height)))
    
    # Draw weapon (gun at bottom center)
    gun_width = 30
    gun_height = 25
    gun_x = (WIDTH - gun_width) // 2
    gun_y = HEIGHT - gun_height - 5
    
    # Gun body
    screen.brush = brushes.color(80, 80, 80)
    screen.draw(shapes.rectangle(gun_x + 10, gun_y + 10, 10, 15))
    
    # Gun barrel
    screen.brush = brushes.color(60, 60, 60)
    screen.draw(shapes.rectangle(gun_x + 12, gun_y, 6, 12))
    
    # Muzzle flash effect - enhanced with multiple layers
    if muzzle_flash > 0:
        flash_brightness = int(255 * (muzzle_flash / 8))
        flash_center_x = gun_x + 15
        flash_center_y = gun_y
        
        # Outer flash glow (orange/yellow)
        screen.brush = brushes.color(flash_brightness, int(flash_brightness * 0.6), 0)
        screen.draw(shapes.circle(flash_center_x, flash_center_y, 8))
        
        # Middle flash layer (bright yellow)
        screen.brush = brushes.color(flash_brightness, flash_brightness, int(flash_brightness * 0.3))
        screen.draw(shapes.circle(flash_center_x, flash_center_y, 5))
        
        # Inner core (white hot center)
        screen.brush = brushes.color(flash_brightness, flash_brightness, flash_brightness)
        screen.draw(shapes.circle(flash_center_x, flash_center_y, 3))
        
        # Flash rays extending from barrel
        if muzzle_flash > 4:
            screen.brush = brushes.color(flash_brightness, int(flash_brightness * 0.8), 0)
            # Top ray
            screen.draw(shapes.rectangle(flash_center_x - 1, flash_center_y - 10, 2, 10))
            # Side rays
            screen.draw(shapes.rectangle(flash_center_x - 8, flash_center_y - 1, 6, 2))
            screen.draw(shapes.rectangle(flash_center_x + 2, flash_center_y - 1, 6, 2))


def render_minimap():
    """Render a small minimap in the corner"""
    global player_x, player_y, player_angle
    
    map_size = 3  # pixels per map tile
    map_offset_x = 5
    map_offset_y = 5
    
    # Draw map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if GAME_MAP[y][x] == 1:
                screen.brush = brushes.color(200, 200, 200)
            else:
                screen.brush = brushes.color(50, 50, 50)
            
            screen.draw(shapes.rectangle(
                map_offset_x + x * map_size,
                map_offset_y + y * map_size,
                map_size - 1,
                map_size - 1
            ))
    
    # Draw enemies
    for enemy in enemies:
        if enemy[2]:  # If alive
            screen.brush = brushes.color(255, 0, 0)
            enemy_map_x = int(map_offset_x + enemy[0] * map_size)
            enemy_map_y = int(map_offset_y + enemy[1] * map_size)
            screen.draw(shapes.circle(enemy_map_x, enemy_map_y, 1))
    
    # Draw player
    screen.brush = brushes.color(0, 255, 0)
    player_map_x = int(map_offset_x + player_x * map_size)
    player_map_y = int(map_offset_y + player_y * map_size)
    screen.draw(shapes.circle(player_map_x, player_map_y, 1))
    
    # Draw direction indicator
    dir_x = player_map_x + int(math.cos(player_angle) * 3)
    dir_y = player_map_y + int(math.sin(player_angle) * 3)
    screen.draw(shapes.line(player_map_x, player_map_y, dir_x, dir_y, 1))


def shoot():
    """Handle shooting mechanic"""
    global weapon_cooldown, muzzle_flash
    
    if weapon_cooldown > 0:
        return
    
    # Set cooldown and muzzle flash
    weapon_cooldown = 10
    muzzle_flash = 8
    
    # Cast ray in player's direction to check for enemy hits
    center_angle = player_angle
    _, _, enemy_idx, enemy_dist = cast_ray(center_angle)
    
    # Check if we hit an enemy
    if enemy_idx is not None and enemy_dist < 5.0:
        enemies[enemy_idx][2] = False  # Kill the enemy


def update_player():
    """Update player position based on input"""
    global player_x, player_y, player_angle, weapon_cooldown, muzzle_flash
    
    # Decrease cooldowns
    if weapon_cooldown > 0:
        weapon_cooldown -= 1
    if muzzle_flash > 0:
        muzzle_flash -= 1
    
    # Rotation
    if io.BUTTON_A in io.held:
        player_angle -= ROTATE_SPEED
    if io.BUTTON_C in io.held:
        player_angle += ROTATE_SPEED
    
    # Shooting
    if io.BUTTON_B in io.pressed:
        shoot()
    
    # Forward/backward movement
    move_x = 0
    move_y = 0
    
    if io.BUTTON_UP in io.held:
        move_x = math.cos(player_angle) * MOVE_SPEED
        move_y = math.sin(player_angle) * MOVE_SPEED
    if io.BUTTON_DOWN in io.held:
        move_x = -math.cos(player_angle) * MOVE_SPEED
        move_y = -math.sin(player_angle) * MOVE_SPEED
    
    # Collision detection
    new_x = player_x + move_x
    new_y = player_y + move_y
    
    # Check if new position is valid
    if 0 <= int(new_x) < MAP_WIDTH and 0 <= int(new_y) < MAP_HEIGHT:
        if GAME_MAP[int(new_y)][int(new_x)] == 0:
            player_x = new_x
            player_y = new_y


def update():
    """Main update loop"""
    # Update game state
    update_player()
    
    # Render
    render_3d_view()
    render_minimap()
    
    # Draw controls help
    screen.brush = brushes.color(255, 255, 255, 200)
    screen.text("UP/DN:Move", 5, HEIGHT - 25)
    screen.text("A/C:Turn B:Shoot", 5, HEIGHT - 15)


if __name__ == "__main__":
    run(update)
