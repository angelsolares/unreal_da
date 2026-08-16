// Keyboard + pointer-lock mouse input.
export class Input {
  constructor(domElement) {
    this.dom = domElement;
    this.keys = new Set();
    this.mouseDX = 0;
    this.mouseDY = 0;
    this.locked = false;
    this.buttons = new Set();
    this.pressed = new Set();   // edge-triggered keys, consumed each frame
    this.clicked = new Set();   // edge-triggered mouse buttons

    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      this.keys.add(e.code);
      this.pressed.add(e.code);
    });
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());

    this.dom.addEventListener('mousedown', (e) => {
      this.buttons.add(e.button);
      this.clicked.add(e.button);
      if (!this.locked) this.dom.requestPointerLock();
    });
    window.addEventListener('mouseup', (e) => this.buttons.delete(e.button));
    this.dom.addEventListener('contextmenu', (e) => e.preventDefault());

    document.addEventListener('pointerlockchange', () => {
      this.locked = document.pointerLockElement === this.dom;
    });
    window.addEventListener('mousemove', (e) => {
      if (!this.locked) return;
      this.mouseDX += e.movementX;
      this.mouseDY += e.movementY;
    });
  }

  down(code) { return this.keys.has(code); }
  justPressed(code) { return this.pressed.has(code); }
  mouseDown(btn) { return this.buttons.has(btn); }
  justClicked(btn) { return this.clicked.has(btn); }

  // Called at the end of each frame.
  consume() {
    this.pressed.clear();
    this.clicked.clear();
    this.mouseDX = 0;
    this.mouseDY = 0;
  }
}
