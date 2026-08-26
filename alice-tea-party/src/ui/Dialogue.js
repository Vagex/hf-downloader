import { audioManager } from '../game/Audio.js';

export class DialogueSystem {
  constructor(questMgr) {
    this.questMgr = questMgr;

    this.modal = document.getElementById('dialogue-modal');
    this.avatar = document.getElementById('dialogue-avatar');
    this.speakerName = document.getElementById('speaker-name');
    this.speakerText = document.getElementById('speaker-text');
    this.optionsContainer = document.getElementById('dialogue-options');
  }

  showDialogue(avatarEmoji, name, text, options) {
    this.avatar.textContent = avatarEmoji;
    this.speakerName.textContent = name;
    this.speakerText.textContent = text;

    this.optionsContainer.innerHTML = '';
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'dialogue-btn';
      btn.textContent = opt.label;
      btn.addEventListener('click', () => {
        this.hideDialogue();
        if (opt.action) opt.action();
      });
      this.optionsContainer.appendChild(btn);
    });

    this.modal.classList.remove('hidden');
  }

  hideDialogue() {
    this.modal.classList.add('hidden');
  }

  triggerCheshireRiddle() {
    audioManager.playMeow();
    this.showDialogue(
      '😸',
      '柴郡猫',
      '“好久不见，爱丽丝！问你个仙境谜题：在疯狂茶会里，当时间掉进了红茶壶，三月兔要怎么知道现在是几点？”',
      [
        {
          label: 'A. 看红茶表面旋转的波纹',
          action: () => {
            alert('“近了！但不对哦～试试看齿轮吧！”');
          }
        },
        {
          label: 'B. 观察旋转的怀表齿轮 ⏰',
          action: () => {
            this.questMgr.completeCheshireRiddle();
            alert('“完全正确！天空的怀表齿轮彩虹桥为你开启了！”');
          }
        },
        {
          label: 'C. 直接问红心王后',
          action: () => {
            alert('“哈哈！小心被王后砍头！”');
          }
        }
      ]
    );
  }
}
