import glm

class Camera:
    def __init__(self, position=(0, 0, 0), yaw=-90, pitch=0):
        self.position = glm.vec3(position)
        self.yaw = yaw
        self.pitch = pitch
        
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)
        
        self.update_camera_vectors()

    def update_camera_vectors(self):
        yaw, pitch = glm.radians(self.yaw), glm.radians(self.pitch)
        
        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)
        
        self.forward = glm.normalize(self.forward)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)

    def get_projection_matrix(self, aspect_ratio, fov=70):
        return glm.perspective(glm.radians(fov), aspect_ratio, 0.1, 2000.0)
