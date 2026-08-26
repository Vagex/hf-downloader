import * as THREE from 'three';
import { GraphicsEngine } from './game/Engine.js';
import { ThirdPersonControls } from './game/Controls.js';
import { PhysicsEngine } from './game/Physics.js';
import { ParticleSystem } from './game/Particles.js';
import { audioManager } from './game/Audio.js';
import { QuestManager } from './game/QuestManager.js';

import { AliceCharacter } from './entities/Alice.js';
import { TeaTableEntity } from './entities/TeaTable.js';
import { CardGuardEntity } from './entities/CardGuard.js';
import { CheshireCatEntity } from './entities/CheshireCat.js';
import { WonderlandEnvironment } from './entities/Environment.js';

import { HUDController } from './ui/HUD.js';
import { DialogueSystem } from './ui/Dialogue.js';
import { PhotoModeStudio } from './ui/PhotoMode.js';

class AliceGameApp {
  constructor() {
    // 1. Engine & Controls
    this.engine = new GraphicsEngine('canvas-container');
    this.controls = new ThirdPersonControls(this.engine.camera, this.engine.renderer.domElement);
    this.physics = new PhysicsEngine();
    this.particles = new ParticleSystem(this.engine.scene);

    // 2. Game Entities
    this.alice = new AliceCharacter(this.engine.scene);
    this.teaTable = new TeaTableEntity(this.engine.scene);
    this.environment = new WonderlandEnvironment(this.engine.scene, this.physics);

    // Cheshire Cat
    this.cheshireCat = new CheshireCatEntity(this.engine.scene, new THREE.Vector3(-15, 0, 15));
    
    // Card Guards
    this.cardGuards = [
      new CardGuardEntity(this.engine.scene, new THREE.Vector3(-14, 0, -20), [
        new THREE.Vector3(-14, 0, -20), new THREE.Vector3(-22, 0, -20),
        new THREE.Vector3(-22, 0, -32), new THREE.Vector3(-14, 0, -32)
      ], 'hearts'),
      new CardGuardEntity(this.engine.scene, new THREE.Vector3(14, 0, -20), [
        new THREE.Vector3(14, 0, -20), new THREE.Vector3(22, 0, -20),
        new THREE.Vector3(22, 0, -32), new THREE.Vector3(14, 0, -32)
      ], 'spades')
    ];

    // 3. UI Systems & Quests
    this.hud = new HUDController();
    this.questMgr = new QuestManager({
      updateInventoryCounts: (inv) => this.hud.updateInventoryCounts(inv),
      updateActiveQuest: (title, desc, fill) => this.hud.updateActiveQuest(title, desc, fill),
      onQuestCompleted: (qId) => {
        const itemEl = document.getElementById(`qitem-${qId.replace('q', '')}`);
        const badgeEl = document.getElementById(`qbadge-${qId.replace('q', '')}`);
        if (badgeEl) {
          badgeEl.textContent = '已完成 ✓';
          badgeEl.classList.add('completed');
        }
      },
      showVictoryModal: () => this.hud.showVictoryModal()
    });

    this.dialogue = new DialogueSystem(this.questMgr);
    this.photoStudio = new PhotoModeStudio(this.engine.renderer, this.engine.scene, this.engine.camera);

    // Add Cheshire Cat riddle interaction
    this.physics.addInteractable(
      'cheshire-riddle',
      this.cheshireCat.group,
      3.0,
      '按 [E] 与柴郡猫对话解谜 😸',
      () => {
        this.dialogue.triggerCheshireRiddle();
      }
    );

    // Initialize UI Event Listeners
    this.initUIListeners();

    // Show start button on loading screen
    setTimeout(() => {
      this.hud.showStartButton();
    }, 800);

    // Clock for delta time
    this.clock = new THREE.Clock();

    // Start Game Loop
    this.animate();
  }

  initUIListeners() {
    // Start Game Button
    document.getElementById('start-btn').addEventListener('click', () => {
      audioManager.init();
      audioManager.startBGM();
      this.hud.hideLoadingScreen();
    });

    // Sound toggle
    document.getElementById('btn-sound').addEventListener('click', () => {
      const isMuted = audioManager.toggleMute();
      document.getElementById('btn-sound').textContent = isMuted ? '🔇' : '🔊';
    });

    // Closet modal toggle
    const closetModal = document.getElementById('closet-modal');
    document.getElementById('btn-closet').addEventListener('click', () => {
      closetModal.classList.remove('hidden');
    });
    document.getElementById('close-closet-modal').addEventListener('click', () => {
      closetModal.classList.add('hidden');
    });

    // Dress Color Selector
    document.querySelectorAll('.color-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const colorHex = parseInt(btn.dataset.color.replace('#', '0x'), 16);
        this.alice.setDressColor(colorHex);
      });
    });

    // Hat Selector
    document.querySelectorAll('.hat-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.hat-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.alice.setHat(btn.dataset.hat);
      });
    });

    // Quests modal toggle
    const questModal = document.getElementById('quest-modal');
    document.getElementById('btn-quests').addEventListener('click', () => {
      questModal.classList.remove('hidden');
    });
    document.getElementById('close-quest-modal').addEventListener('click', () => {
      questModal.classList.add('hidden');
    });

    // Photo Mode toggle
    document.getElementById('btn-photo').addEventListener('click', () => {
      this.photoStudio.enterPhotoMode();
    });

    // Replay/Continue button
    document.getElementById('victory-replay-btn').addEventListener('click', () => {
      document.getElementById('victory-modal').classList.add('hidden');
    });

    // Interaction Trigger (E key or Touch Action button)
    const triggerCurrentInteraction = () => {
      const nearest = this.physics.getNearestInteractable(this.alice.group.position, this.alice.scale);
      if (nearest && nearest.onInteract) {
        nearest.onInteract(this.alice, this.questMgr);
      }
    };

    window.addEventListener('keydown', (e) => {
      if (e.code === 'KeyE') {
        triggerCurrentInteraction();
      }
    });

    document.getElementById('touch-action-btn').addEventListener('click', () => {
      triggerCurrentInteraction();
    });

    document.getElementById('touch-jump-btn').addEventListener('click', () => {
      this.alice.jump();
    });

    // Virtual Joystick Touch Setup
    this.setupJoystick();
  }

  setupJoystick() {
    const zone = document.getElementById('joystick-zone');
    const stick = document.getElementById('joystick-stick');
    if (!zone || !stick) return;

    let active = false;
    let startX = 0, startY = 0;

    const handleStart = (e) => {
      active = true;
      const touch = e.touches ? e.touches[0] : e;
      startX = touch.clientX;
      startY = touch.clientY;
    };

    const handleMove = (e) => {
      if (!active) return;
      const touch = e.touches ? e.touches[0] : e;
      const dx = touch.clientX - startX;
      const dy = touch.clientY - startY;

      const maxDist = 45;
      const dist = Math.hypot(dx, dy);
      const angle = Math.atan2(dy, dx);

      const clampedDist = Math.min(dist, maxDist);
      const moveX = Math.cos(angle) * clampedDist;
      const moveY = Math.sin(angle) * clampedDist;

      stick.style.transform = `translate(${moveX}px, ${moveY}px)`;

      // Set vector (-1 to 1)
      this.controls.setJoystickVector(moveX / maxDist, moveY / maxDist);
    };

    const handleEnd = () => {
      active = false;
      stick.style.transform = 'translate(0px, 0px)';
      this.controls.setJoystickVector(0, 0);
    };

    zone.addEventListener('touchstart', handleStart, { passive: true });
    window.addEventListener('touchmove', handleMove, { passive: true });
    window.addEventListener('touchend', handleEnd, { passive: true });
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const delta = Math.min(this.clock.getDelta(), 0.1);

    // 1. Get Alice Movement & Update Controls
    const moveDir = this.controls.getMovementVector();
    if (this.controls.keys.jump) {
      this.alice.jump();
    }

    // 2. Update Alice
    this.alice.update(delta, moveDir, this.physics);

    // 3. Update Camera to follow Alice
    this.controls.updateCamera(this.alice.group.position, this.alice.scale);

    // 4. Update Entities & Environment
    this.teaTable.update(delta);
    this.cheshireCat.update(delta);
    this.cardGuards.forEach(g => g.update(delta));
    this.environment.update(delta);
    this.particles.update(delta);

    // 5. Update Interactive Prompts
    const nearestInteractable = this.physics.getNearestInteractable(this.alice.group.position, this.alice.scale);
    if (nearestInteractable) {
      this.hud.setActionPrompt(nearestInteractable.promptText);
    } else {
      this.hud.setActionPrompt(null);
    }

    // 6. Update Size Badge HUD
    this.hud.updateSizeBadge(this.alice.scale);

    // 7. Render Minimap
    this.hud.renderMinimap(this.alice.group.position, this.cardGuards);

    // 8. Render WebGL Frame
    this.engine.render();
  }
}

// Instantiate App when DOM Ready
window.addEventListener('DOMContentLoaded', () => {
  new AliceGameApp();
});
