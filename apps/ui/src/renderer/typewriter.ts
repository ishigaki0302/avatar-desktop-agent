/**
 * Typewriter engine with lipsync hooks (Plan A: typewriter-synced).
 *
 * Usage:
 *   const tw = new Typewriter(el, { onMouthOpen, onMouthClose, onDone });
 *   tw.play("こんにちは！元気ですか？");
 */

export interface TypewriterConfig {
  charMs?: number;          // ms per character (default 45)
  lipsyncToggleMs?: number; // mouth toggle interval ms (default 120)
  pauseCommaMs?: number;    // pause after 、(default 150)
  pauseSentenceMs?: number; // pause after 。！？(default 400)
  pauseNewlineMs?: number;  // pause after \n (default 400)
}

export interface TypewriterCallbacks {
  onMouthOpen: () => void;
  onMouthClose: () => void;
  onDone: () => void;
}

const SENTENCE_END = new Set(["。", "！", "？", "!", "?"]);
const COMMA = new Set(["、", ","]);

export class Typewriter {
  private el: HTMLElement;
  private cfg: Required<TypewriterConfig>;
  private callbacks: TypewriterCallbacks;
  private abortController: AbortController | null = null;

  constructor(el: HTMLElement, callbacks: TypewriterCallbacks, cfg: TypewriterConfig = {}) {
    this.el = el;
    this.callbacks = callbacks;
    this.cfg = {
      charMs:          cfg.charMs          ?? 45,
      lipsyncToggleMs: cfg.lipsyncToggleMs ?? 120,
      pauseCommaMs:    cfg.pauseCommaMs    ?? 150,
      pauseSentenceMs: cfg.pauseSentenceMs ?? 400,
      pauseNewlineMs:  cfg.pauseNewlineMs  ?? 400,
    };
  }

  stop() {
    this.abortController?.abort();
    this.abortController = null;
    this.callbacks.onMouthClose();
  }

  async play(text: string) {
    this.stop();
    this.abortController = new AbortController();
    const signal = this.abortController.signal;

    this.el.textContent = "";
    this.callbacks.onMouthOpen();

    let mouthOpen = true;
    let lipsyncTimer = setInterval(() => {
      if (signal.aborted) { clearInterval(lipsyncTimer); return; }
      mouthOpen = !mouthOpen;
      if (mouthOpen) this.callbacks.onMouthOpen();
      else this.callbacks.onMouthClose();
    }, this.cfg.lipsyncToggleMs);

    const sleep = (ms: number) =>
      new Promise<void>((res, rej) => {
        const t = setTimeout(res, ms);
        signal.addEventListener("abort", () => { clearTimeout(t); rej(new DOMException("Aborted", "AbortError")); }, { once: true });
      });

    try {
      for (const char of text) {
        if (signal.aborted) break;

        if (char === "\n") {
          this.el.appendChild(document.createElement("br"));
          clearInterval(lipsyncTimer);
          this.callbacks.onMouthClose();
          await sleep(this.cfg.pauseNewlineMs);
          if (!signal.aborted) {
            mouthOpen = true;
            this.callbacks.onMouthOpen();
            lipsyncTimer = setInterval(() => {
              if (signal.aborted) { clearInterval(lipsyncTimer); return; }
              mouthOpen = !mouthOpen;
              if (mouthOpen) this.callbacks.onMouthOpen();
              else this.callbacks.onMouthClose();
            }, this.cfg.lipsyncToggleMs);
          }
          continue;
        }

        this.el.appendChild(document.createTextNode(char));
        await sleep(this.cfg.charMs);

        if (SENTENCE_END.has(char)) {
          clearInterval(lipsyncTimer);
          this.callbacks.onMouthClose();
          await sleep(this.cfg.pauseSentenceMs);
          if (!signal.aborted) {
            mouthOpen = true;
            this.callbacks.onMouthOpen();
            lipsyncTimer = setInterval(() => {
              if (signal.aborted) { clearInterval(lipsyncTimer); return; }
              mouthOpen = !mouthOpen;
              if (mouthOpen) this.callbacks.onMouthOpen();
              else this.callbacks.onMouthClose();
            }, this.cfg.lipsyncToggleMs);
          }
        } else if (COMMA.has(char)) {
          clearInterval(lipsyncTimer);
          this.callbacks.onMouthClose();
          await sleep(this.cfg.pauseCommaMs);
          if (!signal.aborted) {
            mouthOpen = true;
            this.callbacks.onMouthOpen();
            lipsyncTimer = setInterval(() => {
              if (signal.aborted) { clearInterval(lipsyncTimer); return; }
              mouthOpen = !mouthOpen;
              if (mouthOpen) this.callbacks.onMouthOpen();
              else this.callbacks.onMouthClose();
            }, this.cfg.lipsyncToggleMs);
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") throw e;
    } finally {
      clearInterval(lipsyncTimer);
      this.callbacks.onMouthClose();
      if (!signal.aborted) this.callbacks.onDone();
    }
  }
}
