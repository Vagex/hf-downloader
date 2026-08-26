import * as THREE from 'three';

export class PhysicsEngine {
  constructor() {
    this.colliders = [];
    this.bounceMushrooms = [];
    this.interactables = [];
  }

  addCollider(mesh, type = 'box', size = null) {
    this.colliders.push({ mesh, type, size });
  }

  addBounceMushroom(mesh, bounceForce = 18) {
    this.bounceMushrooms.push({ mesh, bounceForce });
  }

  addInteractable(id, mesh, radius, promptText, onInteract) {
    this.interactables.push({
      id,
      mesh,
      radius,
      promptText,
      onInteract,
      active: true
    });
  }

  removeInteractable(id) {
    this.interactables = this.interactables.filter(item => item.id !== id);
  }

  checkMushroomBounce(alicePos, velocityY) {
    for (const m of this.bounceMushrooms) {
      const distance = alicePos.distanceTo(m.mesh.position);
      if (distance < 2.2 && Math.abs(alicePos.y - m.mesh.position.y) < 1.8) {
        return m.bounceForce;
      }
    }
    return null;
  }

  getNearestInteractable(alicePos, aliceScale = 1.0) {
    let nearest = null;
    let minDistance = Infinity;

    for (const item of this.interactables) {
      if (!item.active || !item.mesh.parent) continue;
      const worldPos = new THREE.Vector3();
      item.mesh.getWorldPosition(worldPos);
      const dist = alicePos.distanceTo(worldPos);

      // Adjust trigger radius based on interaction type & Alice scale
      const effectiveRadius = item.radius * (aliceScale < 0.5 ? 1.5 : 1.0);

      if (dist < effectiveRadius && dist < minDistance) {
        minDistance = dist;
        nearest = item;
      }
    }

    return nearest;
  }

  // Handle player collision against world objects & platform bounds
  resolveTerrainCollision(playerPos, playerRadius = 0.6) {
    // Keep within world bounds (-60 to 60)
    const bounds = 58;
    playerPos.x = Math.max(-bounds, Math.min(bounds, playerPos.x));
    playerPos.z = Math.max(-bounds, Math.min(bounds, playerPos.z));

    // Simple cylinder/box obstacle colliders
    for (const col of this.colliders) {
      if (!col.mesh.visible) continue;
      const colPos = new THREE.Vector3();
      col.mesh.getWorldPosition(colPos);

      if (col.type === 'box') {
        const dx = playerPos.x - colPos.x;
        const dz = playerPos.z - colPos.z;
        const halfW = (col.size ? col.size.x : 2) / 2 + playerRadius;
        const halfD = (col.size ? col.size.z : 2) / 2 + playerRadius;

        if (Math.abs(dx) < halfW && Math.abs(dz) < halfD && playerPos.y < colPos.y + 3) {
          // Push out
          const overlapX = halfW - Math.abs(dx);
          const overlapZ = halfD - Math.abs(dz);
          if (overlapX < overlapZ) {
            playerPos.x += dx > 0 ? overlapX : -overlapX;
          } else {
            playerPos.z += dz > 0 ? overlapZ : -overlapZ;
          }
        }
      } else if (col.type === 'cylinder') {
        const distXZ = Math.hypot(playerPos.x - colPos.x, playerPos.z - colPos.z);
        const minDist = (col.size ? col.size.r : 1.5) + playerRadius;
        if (distXZ < minDist && playerPos.y < colPos.y + 4) {
          const angle = Math.atan2(playerPos.z - colPos.z, playerPos.x - colPos.x);
          playerPos.x = colPos.x + Math.cos(angle) * minDist;
          playerPos.z = colPos.z + Math.sin(angle) * minDist;
        }
      }
    }
  }
}
