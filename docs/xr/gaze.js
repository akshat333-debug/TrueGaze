// Real-time port of truegaze/motion.py: the same saccade main sequence, blink profile, lid follow,
// soft-tissue keys, drift, micro-saccades and pupil hippus, driven by a live target instead of a script.
// Angles in degrees: yaw > 0 toward the character's left, pitch > 0 up (as in motion.py).

export const saccadeDuration = (amp) => 0.025 + 0.0024 * amp; // s, main sequence (motion.py)
const minJerk = (t) => { t = Math.min(Math.max(t, 0), 1); return t ** 3 * (10 - 15 * t + 6 * t * t); };
export const saccadeProfile = (t) => { t = Math.min(Math.max(t, 0), 1); return 0.35 * minJerk(t) + 0.65 * (1 - Math.cos(Math.PI * t)) / 2; };

export function blinkProfile(t) { // lid closure 0..1, t seconds since blink start (motion.py blink_profile)
  const close = 0.10, hold = 0.03, open = 0.24;
  if (t < 0) return 0;
  if (t < close) return minJerk(t / close);
  if (t < close + hold) return 1;
  return Math.max(0, 1 - minJerk((t - close - hold) / open));
}

const clip = (x, a, b) => Math.min(Math.max(x, a), b);

export function lids(yaw, pitch) { // motion.py lids()
  return {
    upper_lid_up: clip(pitch / 25, 0, 1), upper_lid_down: clip(-pitch / 30, 0, 1),
    lower_lid_up: -0.8 * clip(-pitch / 30, 0, 1) + 0.15 * clip(pitch / 25, 0, 1) + 0.1 * clip(Math.abs(yaw) / 30, 0, 1),
    brow_raise: clip(pitch / 30, 0, 0.8), brow_lower: clip(-pitch / 45, 0, 0.45),
  };
}

export function softTissue(side, yaw, pitch) { // motion.py soft_tissue(): bulge grows as (angle/limit)^2, drag linearly
  const toNose = side === "left" ? -yaw : yaw, out = {};
  for (const [name, angle, limit] of [["in", toNose, 32], ["out", -toNose, 32], ["up", pitch, 24], ["down", -pitch, 24]]) {
    const w = clip(angle / limit, 0, 1);
    out[`bulge_${name}_${side}`] = w * w; out[`drag_${name}_${side}`] = w;
  }
  return out;
}

const gauss = () => Math.sqrt(-2 * Math.log(1 - Math.random())) * Math.cos(2 * Math.PI * Math.random());

export class Gaze {
  constructor() {
    this.now = 0; this.natural = true;
    this.pos = [0, 0]; this.from = [0, 0]; this.goal = [0, 0]; this.start = -1; this.dur = 0;
    this.pending = null;           // corrective saccade waiting to fire (natural mode)
    this.drift = [0, 0]; this.micro = [0, 0]; this.nextMicro = 1; this.ready = 0;
    this.blinks = []; this.nextBlink = 2 + 3 * Math.random();
    this.last = null;              // last saccade, for the on-screen readout
  }

  blink(strength = 1) { this.blinks.push([this.now, strength]); }

  saccade(to, amp) {
    this.from = [...this.pos]; this.goal = to; this.start = this.now; this.dur = saccadeDuration(amp);
    this.ready = this.now + this.dur + 0.15; // refractory: a new saccade waits for the eye to settle
    this.last = { amp, ms: 1000 * this.dur };
  }

  // target: wanted gaze direction [yaw, pitch] (degrees, head frame); dt seconds
  update(target, dt) {
    this.now += dt;
    const t = this.now;
    const err = Math.hypot(target[0] - this.goal[0], target[1] - this.goal[1]);
    if (this.pending && t >= this.pending.at) { const p = this.pending; this.pending = null; this.saccade(p.to, Math.hypot(p.to[0] - this.pos[0], p.to[1] - this.pos[1])); }
    else if (!this.pending && err > 1.0 && t >= this.ready) {
      const amp = Math.hypot(target[0] - this.pos[0], target[1] - this.pos[1]);
      if (amp > 20) this.blink();
      if (this.natural && amp > 12) { // land 6-12 % short, correct 150-220 ms later
        const s = 0.88 + 0.06 * Math.random();
        this.saccade([this.pos[0] + s * (target[0] - this.pos[0]), this.pos[1] + s * (target[1] - this.pos[1])], amp * s);
        this.pending = { at: t + 0.15 + 0.07 * Math.random(), to: target };
      } else this.saccade([...target], amp);
    }
    if (this.start >= 0) {
      const tau = (t - this.start) / this.dur;
      let s = saccadeProfile(tau);
      const after = t - this.start - this.dur; // small overshoot settling back (glissade)
      if (after > 0) s += 0.04 * Math.exp(-after / 0.025) * Math.sin(Math.PI * Math.min(after / 0.06, 1));
      this.pos = [this.from[0] + s * (this.goal[0] - this.from[0]), this.from[1] + s * (this.goal[1] - this.from[1])];
    }
    // fixational eye movement: drift (random walk pulled back) and micro-saccades, as in render_clip
    const k = Math.exp(-dt / 0.4);
    this.drift = this.drift.map((d) => k * d + gauss() * 0.05 * Math.sqrt(dt * 30));
    if (t > this.nextMicro) { this.micro = this.micro.map((m) => 0.6 * (m * 0.5 + gauss() * 0.35)); this.nextMicro = t + 0.6 + Math.random(); }
    // spontaneous blinks every 3-6 s; in natural mode about one in four stops short
    if (t > this.nextBlink) {
      if (this.blinks.every(([b]) => Math.abs(t - b) > 0.8)) this.blink(this.natural && Math.random() < 0.25 ? 0.6 + 0.25 * Math.random() : 1);
      this.nextBlink = t + 3 + 3 * Math.random();
    }
    this.blinks = this.blinks.filter(([b]) => t - b < 0.5);
    const closure = Math.max(0, ...this.blinks.map(([b, s]) => s * blinkProfile(t - b)));
    const yaw = this.pos[0] + this.drift[0] + this.micro[0];
    const pitch = this.pos[1] + this.drift[1] + this.micro[1] - 4 * closure; // eyes dip during a blink (Bell)
    return { yaw, pitch, closure, pupil: -0.9 + 0.2 * Math.sin(2 * Math.PI * 0.35 * t) + 0.1 * Math.sin(2 * Math.PI * 0.9 * t + 1) };
  }
}

// Shape-key weights for one frame, the same mapping render.py keyframes
export function weights(yaw, pitch, closure, eyeAngles, natural, t) {
  const w = { socket_left: 1, socket_right: 1 };
  const l = lids(yaw, pitch);
  for (const side of ["left", "right"]) {
    w[`blink_${side}`] = closure;
    w[`blink_mid_${side}`] = 4 * closure * (1 - closure);
    for (const [name, v] of Object.entries(l)) w[`${name}_${side}`] = v;
    w[`brow_lower_${side}`] = Math.min(l.brow_lower + 0.18 * closure, 0.6);
    w[`lower_lid_up_${side}`] = Math.min(l.lower_lid_up + 0.10 * closure, 0.4);
    Object.assign(w, softTissue(side, eyeAngles[side][0], eyeAngles[side][1]));
  }
  if (natural) w.brow_raise_right *= 0.85; // one brow rises a little less (motion.py natural mode)
  return w;
}
