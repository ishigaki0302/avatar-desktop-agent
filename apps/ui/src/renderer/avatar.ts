/**
 * Avatar renderer using hand-drawn images.
 *
 * Images (assets/sprites/):
 *   alice_normal.jpg     — default (eyes open, mouth closed)
 *   alice_mouth_open.jpg — lipsync mouth open
 *   alice_eyes_closed.jpg — blink frame
 *
 * Clipping: all source images are 1000×1000.
 * The drawn character occupies x=122–725, y=90–701 → crop w=603, h=611.
 */
import type { Emotion, Motion } from "@avatar-agent/schema";

// __SPRITE_BASE__ is injected by esbuild (absolute path to assets/sprites).
declare const __SPRITE_BASE__: string;
const SPRITE_BASE: string =
  typeof __SPRITE_BASE__ !== "undefined" ? __SPRITE_BASE__ : "../../assets/sprites";

// Source crop region (pixels, within 1000×1000 source images)
const CROP_X = 122;
const CROP_Y = 90;
const CROP_W = 603;
const CROP_H = 611;

const IMG_NORMAL      = `${SPRITE_BASE}/alice_normal.jpg`;
const IMG_MOUTH_OPEN  = `${SPRITE_BASE}/alice_mouth_open.jpg`;
const IMG_EYES_CLOSED = `${SPRITE_BASE}/alice_eyes_closed.jpg`;

// Blink timing
const BLINK_INTERVAL_MIN_MS = 3000;
const BLINK_INTERVAL_MAX_MS = 6000;
const BLINK_DURATION_MS     = 120;

export class AvatarRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private mouthOpen = false;
  private eyesClosed = false;
  private imageCache = new Map<string, HTMLImageElement | null>();
  private blinkTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(canvas: HTMLCanvasElement, _fps = 8) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d")!;
    void this.preloadAll();
    this.scheduleBlink();
  }

  setEmotion(_emotion: Emotion) {
    // Single set of hand-drawn images — emotion expressed via speech bubble
    this.render();
  }

  setMouthOpen(open: boolean) {
    this.mouthOpen = open;
    this.render();
  }

  playMotion(_motion: Motion) {
    // No separate motion sprites; motion intent is expressed via speech bubble
    this.render();
  }

  // ── Private ────────────────────────────────────────────────────────────────

  private render() {
    const src = this.eyesClosed
      ? IMG_EYES_CLOSED
      : this.mouthOpen
        ? IMG_MOUTH_OPEN
        : IMG_NORMAL;

    const img = this.imageCache.get(src);
    if (!img) return; // still loading; preloadAll triggers render when ready

    const w = this.canvas.width;
    const h = this.canvas.height;
    this.ctx.clearRect(0, 0, w, h);
    this.ctx.drawImage(img, CROP_X, CROP_Y, CROP_W, CROP_H, 0, 0, w, h);
  }

  private scheduleBlink() {
    const delay =
      BLINK_INTERVAL_MIN_MS +
      Math.random() * (BLINK_INTERVAL_MAX_MS - BLINK_INTERVAL_MIN_MS);

    this.blinkTimer = setTimeout(() => {
      this.eyesClosed = true;
      this.render();
      setTimeout(() => {
        this.eyesClosed = false;
        this.render();
        this.scheduleBlink();
      }, BLINK_DURATION_MS);
    }, delay);
  }

  private async preloadAll() {
    await Promise.all([
      this.loadImage(IMG_NORMAL),
      this.loadImage(IMG_MOUTH_OPEN),
      this.loadImage(IMG_EYES_CLOSED),
    ]);
    this.render();
  }

  private loadImage(src: string): Promise<HTMLImageElement | null> {
    if (this.imageCache.has(src)) return Promise.resolve(this.imageCache.get(src)!);
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => { this.imageCache.set(src, img); resolve(img); };
      img.onerror = () => { this.imageCache.set(src, null); resolve(null); };
      img.src = src;
    });
  }
}
