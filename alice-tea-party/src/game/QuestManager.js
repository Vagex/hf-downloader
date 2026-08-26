import confetti from 'canvas-confetti';
import { audioManager } from './Audio.js';

export class QuestManager {
  constructor(uiCallbacks) {
    this.ui = uiCallbacks;

    this.inventory = {
      sugar: 0,
      macaron: 0,
      tea: 0,
      rosesPainted: 0,
      keys: 0
    };

    this.quests = {
      q1: { id: 'q1', title: '1. 搜集茶会点心', completed: false },
      q2: { id: 'q2', title: '2. 刷红白玫瑰', completed: false },
      q3: { id: 'q3', title: '3. 柴郡猫的谜题', completed: false },
      q4: { id: 'q4', title: '4. 三月兔的时间钥匙', completed: false }
    };

    this.currentQuestId = 'q1';
    this.gameCompleted = false;
  }

  collectItem(type) {
    audioManager.playCollect();
    if (type === 'sugar') this.inventory.sugar++;
    if (type === 'macaron') this.inventory.macaron++;
    if (type === 'tea') this.inventory.tea++;
    if (type === 'key') this.inventory.keys++;

    this.updateInventoryUI();
    this.checkQuestProgress();
  }

  paintRose() {
    audioManager.playPaint();
    this.inventory.rosesPainted++;
    this.updateInventoryUI();
    this.checkQuestProgress();
  }

  completeCheshireRiddle() {
    audioManager.playMeow();
    this.quests.q3.completed = true;
    this.ui.onQuestCompleted('q3');
    this.switchNextActiveQuest();
  }

  checkQuestProgress() {
    // Check Q1
    if (!this.quests.q1.completed && this.inventory.sugar >= 3 && this.inventory.macaron >= 3 && this.inventory.tea >= 2) {
      this.quests.q1.completed = true;
      audioManager.playFanfare();
      this.ui.onQuestCompleted('q1');
      this.switchNextActiveQuest();
    }

    // Check Q2
    if (!this.quests.q2.completed && this.inventory.rosesPainted >= 4) {
      this.quests.q2.completed = true;
      audioManager.playFanfare();
      this.ui.onQuestCompleted('q2');
      this.switchNextActiveQuest();
    }

    // Check Q4
    if (!this.quests.q4.completed && this.inventory.keys >= 1) {
      this.quests.q4.completed = true;
      audioManager.playFanfare();
      this.ui.onQuestCompleted('q4');
      this.switchNextActiveQuest();
    }

    // Check Victory
    if (Object.values(this.quests).every(q => q.completed) && !this.gameCompleted) {
      this.triggerVictory();
    }
  }

  switchNextActiveQuest() {
    if (!this.quests.q1.completed) {
      this.currentQuestId = 'q1';
      this.ui.updateActiveQuest('1. 搜集茶会点心', '在中央大茶几周边收集 3 块方糖、3 个马卡龙和 2 份茶叶。', (this.inventory.sugar + this.inventory.macaron + this.inventory.tea) / 8 * 100);
    } else if (!this.quests.q2.completed) {
      this.currentQuestId = 'q2';
      this.ui.updateActiveQuest('2. 给白玫瑰涂红', '在玫瑰园中找到 4 朵白玫瑰并刷成红色，注意巡逻的扑克牌侍卫！', (this.inventory.rosesPainted / 4) * 100);
    } else if (!this.quests.q3.completed) {
      this.currentQuestId = 'q3';
      this.ui.updateActiveQuest('3. 柴郡猫的谜题', '在仙境迷雾中寻找发光的柴郡猫笑脸，解开谜题开启天空彩虹桥！', 0);
    } else if (!this.quests.q4.completed) {
      this.currentQuestId = 'q4';
      this.ui.updateActiveQuest('4. 三月兔的时间钥匙', '踏上旋转的怀表齿轮浮岛，获取高空宝箱中的黄金时间钥匙！', (this.inventory.keys / 1) * 100);
    } else {
      this.ui.updateActiveQuest('🎉 仙境茶会圆满成功！', '自由探索爱丽丝的茶话世界，开启拍照模式留下梦幻纪念。', 100);
    }
  }

  updateInventoryUI() {
    this.ui.updateInventoryCounts(this.inventory);
    this.switchNextActiveQuest();
  }

  triggerVictory() {
    this.gameCompleted = true;
    audioManager.playFanfare();
    confetti({
      particleCount: 150,
      spread: 80,
      origin: { y: 0.6 }
    });
    this.ui.showVictoryModal();
  }
}
