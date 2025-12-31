import glm

def check_collision(pos, voxels):
    # pos is (x, y, z)
    ix, iy, iz = int(pos.x), int(pos.y), int(pos.z)
    if 0 <= ix < voxels.shape[0] and 0 <= iy < voxels.shape[1] and 0 <= iz < voxels.shape[2]:
        return voxels[ix, iy, iz] != 0
    return False

def resolve_collisions(entity, voxels, dt):
    # Simple axis-aligned collision resolution
    for i in range(3): # X, Y, Z
        entity.position[i] += entity.velocity[i] * dt
        # Check collision for this axis
        # (This is a very simplified version)
        pass
