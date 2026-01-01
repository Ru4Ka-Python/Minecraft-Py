"""
Particle system for Minecraft clone.
Handles particles like dust, smoke, hearts, stars, and more.
"""

from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass
from PIL import Image, ImageDraw
import numpy as np
import random
import math

from ui.elements import TextureManager


class Particle:
    """Individual particle entity."""
    
    def __init__(self, position: Tuple[float, float, float], particle_type: str = 'dust',
                 velocity: Tuple[float, float, float] = None, lifetime: float = 1.0,
                 size: float = 1.0, color: Tuple[int, int, int] = (255, 255, 255)):
        """Initialize particle."""
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.array(velocity if velocity else [0, 0, 0], dtype=np.float32)
        
        self.particle_type = particle_type
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.color = color
        
        # Physics
        self.gravity = 0.0
        self.friction = 0.98
        self.active = True
        self.alpha = 1.0
    
    def update(self, delta_time: float) -> None:
        """Update particle state."""
        if not self.active:
            return
        
        # Apply gravity
        self.velocity[1] -= self.gravity * delta_time
        
        # Apply friction
        self.velocity *= self.friction
        
        # Update position
        self.position += self.velocity * delta_time * 60
        
        # Update lifetime
        self.lifetime -= delta_time
        
        if self.lifetime <= 0:
            self.active = False
        
        # Update alpha
        self.alpha = self.lifetime / self.max_lifetime
    
    def get_model_matrix(self, camera) -> np.ndarray:
        """Get billboard model matrix for rendering."""
        # Create billboarding matrix (always faces camera)
        matrix = np.eye(4, dtype=np.float32)
        
        matrix[0, 3] = self.position[0]
        matrix[1, 3] = self.position[1]
        matrix[2, 3] = self.position[2]
        
        return matrix


class ParticleSystem:
    """Particle system manager."""
    
    def __init__(self):
        """Initialize particle system."""
        self.particles: List[Particle] = []
        self.max_particles = 1000
        
        # Particle textures
        self._load_textures()
    
    def _load_textures(self) -> None:
        """Load particle textures."""
        self.textures: Dict[str, Image.Image] = {}
        
        # Try to load from assets
        particle_img = TextureManager.get('particles')
        if particle_img:
            # Extract individual particles from sheet
            self.textures['dust'] = self._extract_particle(particle_img, 0, 0)
            self.textures['smoke'] = self._extract_particle(particle_img, 1, 0)
            self.textures['spell'] = self._extract_particle(particle_img, 2, 0)
            self.textures['crit'] = self._extract_particle(particle_img, 3, 0)
            self.textures['heart'] = self._extract_particle(particle_img, 0, 1)
            self.textures['note'] = self._extract_particle(particle_img, 1, 1)
            self.textures['enchant'] = self._extract_particle(particle_img, 2, 1)
        else:
            # Create placeholder textures
            self.textures['dust'] = self._create_circle_texture((150, 150, 150), 4)
            self.textures['smoke'] = self._create_circle_texture((100, 100, 100), 8)
            self.textures['heart'] = self._create_heart_texture()
            self.textures['crit'] = self._create_crit_texture()
    
    def _extract_particle(self, sheet: Image.Image, x: int, y: int) -> Image.Image:
        """Extract a single particle from a sprite sheet."""
        size = 8  # Standard particle size
        return sheet.crop((x * size, y * size, (x + 1) * size, (y + 1) * size))
    
    def _create_circle_texture(self, color: Tuple[int, int, int], radius: int) -> Image.Image:
        """Create a circular texture."""
        size = radius * 2
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        draw.ellipse([0, 0, size - 1, size - 1], fill=(*color, 255))
        
        return img
    
    def _create_heart_texture(self) -> Image.Image:
        """Create heart texture."""
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        draw.ellipse([0, 2, 6, 8], fill=(255, 0, 0, 255))
        draw.ellipse([10, 2, 16, 8], fill=(255, 0, 0, 255))
        draw.polygon([(2, 8), (14, 8), (8, 15)], fill=(255, 0, 0, 255))
        
        return img
    
    def _create_crit_texture(self) -> Image.Image:
        """Create crit particle texture."""
        img = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        draw.polygon([(4, 0), (6, 4), (4, 8), (2, 4)], fill=(255, 255, 255, 255))
        
        return img
    
    def spawn(self, position: Tuple[float, float, float], velocity: Tuple[float, float, float] = None,
              particle_type: str = 'dust', count: int = 1, **kwargs) -> List[Particle]:
        """Spawn particles at a position."""
        spawned = []
        
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                # Remove oldest particle
                self.particles = [p for p in self.particles if p.active]
            
            # Randomize velocity
            if velocity:
                vx, vy, vz = velocity
            else:
                vx = random.uniform(-0.1, 0.1)
                vy = random.uniform(0, 0.2)
                vz = random.uniform(-0.1, 0.1)
            
            particle = Particle(
                position=position,
                particle_type=particle_type,
                velocity=(vx, vy, vz),
                **kwargs
            )
            
            self.particles.append(particle)
            spawned.append(particle)
        
        return spawned
    
    def spawn_dust(self, position: Tuple[float, float, float], count: int = 5,
                   color: Tuple[int, int, int] = (150, 150, 150)) -> List[Particle]:
        """Spawn dust particles."""
        return self.spawn(
            position=position,
            particle_type='dust',
            count=count,
            lifetime=0.5,
            size=1.0,
            color=color
        )
    
    def spawn_smoke(self, position: Tuple[float, float, float], count: int = 3) -> List[Particle]:
        """Spawn smoke particles."""
        particles = []
        for _ in range(count):
            p = self.spawn(
                position=(position[0], position[1] + random.uniform(0, 0.5), position[2]),
                particle_type='smoke',
                count=1,
                velocity=(random.uniform(-0.05, 0.05), random.uniform(0.1, 0.2), random.uniform(-0.05, 0.05)),
                lifetime=1.0,
                size=1.0
            )
            particles.extend(p)
        return particles
    
    def spawn_hearts(self, position: Tuple[float, float, float], count: int = 3) -> List[Particle]:
        """Spawn healing hearts."""
        return self.spawn(
            position=(position[0], position[1] + 1, position[2]),
            particle_type='heart',
            count=count,
            velocity=(random.uniform(-0.1, 0.1), random.uniform(0.1, 0.3), random.uniform(-0.1, 0.1)),
            lifetime=1.0,
            size=1.0,
            color=(255, 50, 50)
        )
    
    def spawn_damage(self, position: Tuple[float, float, float], amount: float,
                     is_critical: bool = False) -> List[Particle]:
        """Spawn damage numbers."""
        particles = []
        
        # Damage number particle
        text = str(int(amount))
        color = (255, 255, 255) if is_critical else (255, 200, 200)
        
        particles.extend(self.spawn(
            position=(position[0], position[1] + 1.5, position[2]),
            particle_type='damage',
            count=1,
            velocity=(random.uniform(-0.05, 0.05), random.uniform(0.2, 0.4), 0),
            lifetime=1.0,
            size=1.0,
            color=color,
            text=text
        ))
        
        # Critical hit particles
        if is_critical:
            self.spawn_crit(position)
        
        return particles
    
    def spawn_crit(self, position: Tuple[float, float, float], count: int = 4) -> List[Particle]:
        """Spawn crit particles."""
        return self.spawn(
            position=position,
            particle_type='crit',
            count=count,
            velocity=(random.uniform(-0.2, 0.2), random.uniform(0.1, 0.3), random.uniform(-0.2, 0.2)),
            lifetime=0.5,
            size=1.0,
            color=(255, 255, 255)
        )
    
    def spawn_explosion(self, position: Tuple[float, float, float], count: int = 20) -> List[Particle]:
        """Spawn explosion particles."""
        particles = []
        
        for _ in range(count):
            velocity = np.random.uniform(-0.5, 0.5, 3)
            velocity[1] = abs(velocity[1])  # Upward bias
            
            particles.extend(self.spawn(
                position=position,
                particle_type='explosion',
                count=1,
                velocity=velocity,
                lifetime=0.5,
                size=2.0,
                color=(200, 100, 50)
            ))
        
        return particles
    
    def spawn_portal(self, position: Tuple[float, float, float], count: int = 5) -> List[Particle]:
        """Spawn portal particles."""
        colors = [(100, 0, 200), (150, 50, 255), (200, 100, 255)]
        
        for _ in range(count):
            color = random.choice(colors)
            particles.extend(self.spawn(
                position=(position[0] + random.uniform(-0.5, 0.5),
                         position[1] + random.uniform(0, 2),
                         position[2] + random.uniform(-0.5, 0.5)),
                particle_type='portal',
                count=1,
                velocity=(random.uniform(-0.1, 0.1), random.uniform(0.05, 0.15), random.uniform(-0.1, 0.1)),
                lifetime=1.0,
                size=1.0,
                color=color
            ))
        
        return particles
    
    def spawn_enchant(self, position: Tuple[float, float, float], count: int = 8) -> List[Particle]:
        """Spawn enchantment particles."""
        colors = [(100, 200, 255), (200, 100, 255), (255, 200, 255)]
        
        for _ in range(count):
            color = random.choice(colors)
            particles.extend(self.spawn(
                position=(position[0] + random.uniform(-0.3, 0.3),
                         position[1] + random.uniform(0, 1.5),
                         position[2] + random.uniform(-0.3, 0.3)),
                particle_type='enchant',
                count=1,
                velocity=(0, random.uniform(0.05, 0.1), 0),
                lifetime=1.5,
                size=1.0,
                color=color
            ))
        
        return particles
    
    def spawn_digging(self, position: Tuple[float, float, float],
                      block_type: str = 'stone') -> List[Particle]:
        """Spawn block breaking particles."""
        color_map = {
            'stone': (120, 120, 120),
            'dirt': (139, 69, 19),
            'wood': (139, 90, 43),
            'grass': (100, 150, 50),
            'sand': (194, 178, 128),
        }
        
        color = color_map.get(block_type, (150, 150, 150))
        
        return self.spawn_dust(position, count=8, color=color)
    
    def spawn_slime(self, position: Tuple[float, float, float], count: int = 6) -> List[Particle]:
        """Spawn slime particles."""
        return self.spawn(
            position=position,
            particle_type='slime',
            count=count,
            velocity=(random.uniform(-0.1, 0.1), random.uniform(0.2, 0.4), random.uniform(-0.1, 0.1)),
            lifetime=0.5,
            size=1.0,
            color=(100, 200, 50)
        )
    
    def spawn_footstep(self, position: Tuple[float, float, float], count: int = 2) -> List[Particle]:
        """Spawn footstep particles (dust when walking)."""
        return self.spawn_dust(position, count=count, color=(150, 150, 150))
    
    def update(self, delta_time: float) -> None:
        """Update all particles."""
        for particle in self.particles:
            particle.update(delta_time)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.active]
    
    def clear(self) -> None:
        """Clear all particles."""
        self.particles.clear()
    
    def render(self, surface: Image.Image, camera) -> None:
        """Render particles to surface."""
        for particle in self.particles:
            if not particle.active:
                continue
            
            # Get texture
            texture = self.textures.get(particle.particle_type)
            if texture is None:
                continue
            
            # Calculate screen position
            screen_pos = self._world_to_screen(particle.position, camera)
            
            if screen_pos is None:
                continue
            
            # Apply size and alpha
            size = int(8 * particle.size * camera.get_fov() / 70)
            
            # Draw particle
            x = int(screen_pos[0] - size // 2)
            y = int(screen_pos[1] - size // 2)
            
            # Apply alpha
            if particle.alpha < 1.0:
                # Create alpha-composited version
                temp = texture.copy()
                temp.putalpha(int(255 * particle.alpha))
                texture = temp
            
            # Scale texture
            texture = texture.resize((size, size), Image.LANCZOS)
            
            # Draw
            surface.paste(texture, (x, y), texture)
    
    def _world_to_screen(self, position: np.ndarray, camera) -> Optional[Tuple[int, int]]:
        """Convert world position to screen coordinates."""
        # View matrix transform
        view_matrix = camera.view_matrix
        proj_matrix = camera.projection_matrix
        
        # Transform position
        pos = np.array([position[0], position[1], position[2], 1.0])
        
        # Apply view matrix
        view_pos = view_matrix @ pos
        
        # Apply projection matrix
        clip_pos = proj_matrix @ view_pos
        
        # Perspective divide
        if clip_pos[3] <= 0:
            return None
        
        ndc_x = clip_pos[0] / clip_pos[3]
        ndc_y = clip_pos[1] / clip_pos[3]
        
        # Convert to screen coordinates
        width, height = camera.window.get_size()
        
        screen_x = (ndc_x + 1) * width / 2
        screen_y = (1 - ndc_y) * height / 2
        
        return (int(screen_x), int(screen_y))
    
    def get_particle_count(self) -> int:
        """Get number of active particles."""
        return len([p for p in self.particles if p.active])
