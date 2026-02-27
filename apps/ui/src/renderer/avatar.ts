/**
 * Avatar renderer using Canvas 2D.
 *
 * Sprite layout (assets/sprites/):
 *   {emotion}_open.png   — mouth open
 *   {emotion}_close.png  — mouth closed
 *   motion_{name}_{N}.png — motion frame N (0-indexed)
 *
 * Falls back to a colored rectangle placeholder when images are missing.
 */
import type { Emotion, Motion } from "@avatar-agent/schema";

// __SPRITE_BASE__ is injected by esbuild (absolute path to assets/sprites).
// Falls back to a relative path for type-checker compatibility.
declare const __SPRITE_BASE__: string;
const SPRITE_BASE: string =
  typeof __SPRITE_BASE__ !== "undefined" ? __SPRITE_BASE__ : "../../assets/sprites";

interface AvatarState {
  emotion: Emotion;
  mouthOpen: boolean;
  motion: Motion;
  motionFrame: number;
  motionTimer: ReturnType<typeof setInterval> | null;
}

const MOTION_FRAMES: Record<Motion, number> = {
  none: 0,
  bow_small: 4,
  nod: 3,
  shake: 4,
  wave: 6,
};

// Placeholder colors per emotion (used when sprites are missing)
const EMOTION_COLORS: Record<Emotion, string> = {
  neutral:   "#a8d8ea",
  happy:     "#ffd700",
  sad:       "#7eb8d4",
  angry:     "#ff7675",
  surprised: "#fd79a8",
  confused:  "#a29bfe",
};

export class AvatarRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private state: AvatarState;
  private imageCache = new Map<string, HTMLImageElement | null>();
  private fps: number;

  constructor(canvas: HTMLCanvasElement, fps = 8) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d")!;
    this.fps = fps;
    this.state = {
      emotion: "neutral",
      mouthOpen: false,
      motion: "none",
      motionFrame: 0,
      motionTimer: null,
    };
    this.render();
  }

  setEmotion(emotion: Emotion) {
    this.state.emotion = emotion;
    this.render();
  }

  setMouthOpen(open: boolean) {
    this.state.mouthOpen = open;
    this.render();
  }

  playMotion(motion: Motion) {
    if (this.state.motionTimer) clearInterval(this.state.motionTimer);
    this.state.motion = motion;
    this.state.motionFrame = 0;

    if (motion === "none" || MOTION_FRAMES[motion] === 0) {
      this.state.motionTimer = null;
      this.render();
      return;
    }

    this.state.motionTimer = setInterval(() => {
      this.state.motionFrame++;
      const maxFrames = MOTION_FRAMES[this.state.motion];
      if (this.state.motionFrame >= maxFrames) {
        clearInterval(this.state.motionTimer!);
        this.state.motionTimer = null;
        this.state.motion = "none";
        this.state.motionFrame = 0;
      }
      this.render();
    }, 1000 / this.fps);
  }

  private render() {
    const { emotion, mouthOpen, motion, motionFrame } = this.state;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Try to load sprite
    const spritePath = motion !== "none"
      ? `${SPRITE_BASE}/motion_${motion}_${motionFrame}.png`
      : `${SPRITE_BASE}/${emotion}_${mouthOpen ? "open" : "close"}.png`;

    this.loadImage(spritePath).then((img) => {
      this.ctx.clearRect(0, 0, w, h);
      if (img) {
        this.ctx.drawImage(img, 0, 0, w, h);
      } else {
        this.drawPlaceholder(emotion, mouthOpen);
      }
    });
  }

  private drawPlaceholder(emotion: Emotion, mouthOpen: boolean) {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;

    ctx.clearRect(0, 0, w, h);

    // Body circle
    ctx.beginPath();
    ctx.arc(w / 2, h / 2 - 20, 120, 0, Math.PI * 2);
    ctx.fillStyle = EMOTION_COLORS[emotion];
    ctx.fill();
    ctx.strokeStyle = "rgba(0,0,0,0.15)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Eyes
    ctx.fillStyle = "#333";
    ctx.beginPath();
    ctx.arc(w / 2 - 35, h / 2 - 30, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(w / 2 + 35, h / 2 - 30, 10, 0, Math.PI * 2);
    ctx.fill();

    // Mouth
    ctx.beginPath();
    if (mouthOpen) {
      ctx.ellipse(w / 2, h / 2 + 20, 28, 18, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#333";
      ctx.fill();
    } else {
      ctx.arc(w / 2, h / 2 + 10, 28, 0, Math.PI);
      ctx.strokeStyle = "#333";
      ctx.lineWidth = 3;
      ctx.stroke();
    }

    // Emotion label (debug)
    ctx.fillStyle = "rgba(0,0,0,0.4)";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(emotion, w / 2, h - 20);
  }

  private async loadImage(src: string): Promise<HTMLImageElement | null> {
    if (this.imageCache.has(src)) return this.imageCache.get(src)!;
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        this.imageCache.set(src, img);
        resolve(img);
      };
      img.onerror = () => {
        this.imageCache.set(src, null);
        resolve(null);
      };
      img.src = src;
    });
  }
}
