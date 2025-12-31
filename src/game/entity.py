import glm

class Entity:
    def __init__(self, position=(0, 0, 0)):
        self.position = glm.vec3(position)
        self.velocity = glm.vec3(0, 0, 0)
        self.rotation = glm.vec3(0, 0, 0)
        self.width = 0.6
        self.height = 1.8
        self.on_ground = False

    def get_aabb(self):
        return (
            self.position.x - self.width / 2, self.position.y, self.position.z - self.width / 2,
            self.position.x + self.width / 2, self.position.y + self.height, self.position.z + self.width / 2
        )

    def update(self, dt, world):
        # Gravity
        self.velocity.y -= 20.0 * dt
        
        # Simple movement/collision placeholder
        self.position += self.velocity * dt
        if self.position.y < 0:
            self.position.y = 0
            self.velocity.y = 0
            self.on_ground = True
            
    def render_shadow(self, renderer):
        # Shadows are circular scaling shadows underneath
        pass
