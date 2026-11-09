"""Cria TODOS os efeitos e a trilha do Short por código (numpy + scipy), sem baixar nada.
Uso: python sons.py saida.wav   → 16 s, 48 kHz, estéreo (depois o render masteriza em -14 LUFS)."""
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR, DUR = 48000, 16.0
N = int(SR * DUR)
rng = np.random.default_rng(42)
fx = np.zeros((N, 2)); mus = np.zeros((N, 2))

def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'highpass', fs=SR, output='sos'), x)
def env(n, a, d, curve=4.0):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * curve / max(d, 1e-4)); return e
def noise(sec): return rng.standard_normal(int(SR * sec))
def place(buf, sig, t_peak, gain=1.0, pan=0.0, peak_at=None):
    """coloca o som com o PICO alinhado ao instante t_peak"""
    sig = np.asarray(sig, float)
    if sig.ndim == 1: sig = np.stack([sig * (1 - max(0, pan)), sig * (1 + min(0, pan))], 1)
    pk = int(np.argmax(np.abs(sig).sum(1))) if peak_at is None else int(peak_at * SR)
    s0 = int(t_peak * SR) - pk
    a, b = max(0, s0), min(N, s0 + len(sig))
    if b > a: buf[a:b] += sig[a - s0:b - s0] * gain

# ---------- efeitos ----------
def whoosh(sec=.32):
    n = int(SR * sec); x = noise(sec); t = np.linspace(0, 1, n)
    lo = bp(x, 300, 1200); hi = bp(x, 1200, 4000)
    e = np.sin(np.pi * t) ** 2
    return (lo * (1 - t) + hi * t) * e * .7
def thunder_crack(big=False):
    sec = 2.6 if big else 1.4
    crack = hp(noise(.12), 900) * env(int(SR * .12), .002, .05, 3)
    rumble = lp(noise(sec), 160 if big else 220, 4) * env(int(SR * sec), .02, sec * .7, 3) * (5 if big else 3)
    out = np.zeros(int(SR * sec)); out[:len(crack)] += crack * 1.4; out += rumble
    return out
def wood_crack():
    out = np.zeros(int(SR * .45))
    for k in range(7):
        s = int(SR * (k * .035 + rng.random() * .02)); c = bp(noise(.06), 500, 2600) * env(int(SR * .06), .001, .03, 5)
        out[s:s + len(c)] += c * (1 - k * .1)
    return out + lp(noise(.45), 400) * env(int(SR * .45), .005, .3) * .6
def brick_crumble():
    sec = .9; out = lp(noise(sec), 700) * env(int(SR * sec), .005, .7, 3) * 1.2
    for k in range(40):
        s = int(SR * rng.random() * .7); g = bp(noise(.04), 600, 3000) * env(int(SR * .04), .001, .02, 5)
        out[s:s + len(g)] += g * rng.uniform(.15, .45)
    return out
def glass_shatter():
    sec = 1.2; n = int(SR * sec); out = hp(noise(sec), 3500) * env(n, .001, .25, 5) * 1.2
    t = np.arange(n) / SR
    for k in range(26):
        f = rng.uniform(2500, 7500); s = rng.uniform(0, .5)
        out += np.sin(2 * np.pi * f * t) * np.exp(-np.maximum(0, t - s) * rng.uniform(8, 20)) * (t > s) * rng.uniform(.05, .18)
    return out
def heavy_thud():
    sec = .9; n = int(SR * sec); t = np.arange(n) / SR
    f = 70 * np.exp(-t * 3) + 38
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .003, .5, 4) * 1.6 + lp(noise(sec), 300) * env(n, .002, .2, 5))
def clang():
    sec = 1.4; n = int(SR * sec); t = np.arange(n) / SR; out = np.zeros(n)
    for f, a, d in [(520, 1, 1.2), (1347, .6, .9), (2210, .45, .6), (3120, .3, .4), (4410, .2, .3)]:
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t * 3.5 / d)
    return out * .5 + hp(noise(sec), 2000) * env(n, .001, .06, 6) * .5
def body_fall():
    sec = .6; n = int(SR * sec); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (60 * np.exp(-t * 4) + 45) * t) * env(n, .004, .3, 5) * 1.1 + lp(noise(sec), 900) * env(n, .003, .15, 5) * .6
def crackle_build(sec=.9):
    n = int(SR * sec); t = np.arange(n) / SR; out = np.zeros(n)
    dens = 40 + 400 * (t / sec) ** 2
    for i in range(n):
        if rng.random() < dens[i] / SR:
            c = hp(noise(.008), 2500) * rng.uniform(.3, 1)
            out[i:i + len(c)] += c[:max(0, min(len(c), n - i))]
    saw = ((t * (110 + 90 * t / sec)) % 1 - .5) * (t / sec) ** 1.5 * .35
    return lp(out, 7000) * .7 + bp(saw, 80, 2000)
def rock_collapse():
    sec = 1.6; n = int(SR * sec); out = lp(noise(sec), 500, 4) * env(n, .02, 1.2, 3) * 3
    for k in range(30):
        s = int(SR * (.05 + rng.random() * 1.0)); g = lp(noise(.12), 900) * env(int(SR * .12), .002, .08, 5)
        out[s:s + len(g)] += g * rng.uniform(.3, .9)
    return out
def riser(sec=2.2):
    n = int(SR * sec); t = np.arange(n) / SR
    f = 200 + 1800 * (t / sec) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * .25 + bp(noise(sec), 800, 6000) * .5 * (t / sec)
    return s * (t / sec) ** 1.5 * np.minimum(1, (sec - t) / .15)
def zap():
    sec = .22; n = int(SR * sec); t = np.arange(n) / SR
    f = 1800 * np.exp(-t * 14) + 200
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .002, .15, 5) * .35 + hp(noise(sec), 3000) * env(n, .001, .05, 6) * .5

for h, brk in [(0.5, wood_crack), (2.5, brick_crumble), (4.5, glass_shatter)]:
    place(fx, whoosh(), h - .2, .8, -.2)
    place(fx, thunder_crack(), h + .01, 1.0)
    place(fx, brk(), h + .03, 1.1, .25)
place(fx, heavy_thud(), 6.55, 1.2)
place(fx, clang(), 6.6, .9, .2)
place(fx, body_fall(), 7.35, 1.1, -.3)
place(fx, crackle_build(), 9.0, .9, peak_at=0.0)
place(fx, thunder_crack(True), 9.92, 1.3)
place(fx, rock_collapse(), 10.2, 1.0, .2)
place(fx, whoosh(.4), 10.5, .7)
place(fx, riser(), 12.6, .7, peak_at=0.0)
place(fx, zap(), 13.9, .8); place(fx, zap(), 15.0, .8)

# ---------- trilha: pulso grave + tambores, tensa de noite, abre no amanhecer ----------
BPM = 100; beat = 60 / BPM; t = np.arange(N) / SR
def note(f, sec, a=.01, d=None):
    n = int(SR * sec); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * env(n, a, d or sec, 3)
def kick():
    n = int(SR * .35); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * env(n, .002, .3, 5)
def tom(f):
    n = int(SR * .4); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * env(n, .002, .3, 5) * .6 + lp(noise(.4), 400) * env(n, .001, .05, 6) * .3
night = lambda x: x < 12.6
dawnmix = np.clip((t - 12.6) / 1.4, 0, 1)
k = 0
while k * beat / 2 < DUR:
    tb = k * beat / 2
    if not (6.82 <= tb < 8.55):                               # silêncio de tambor no chão
        place(mus, note(41.2 if night(tb) else 55, beat / 2 * .9, .005, .25) * .55, tb, 1, peak_at=0)  # pulso grave (mi → lá)
    if k % 2 == 0 and not (6.82 <= tb < 8.55): place(mus, kick(), tb, .9, peak_at=0)
    if k % 8 == 6 and tb < 12.6 and not (6.82 <= tb < 8.55): place(mus, tom(110), tb, 1, -.3, peak_at=0); place(mus, tom(90), tb + beat / 2, 1, .3, peak_at=0)
    k += 1
pad_night = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([82.4, 98.0, 123.5, 164.8])) * .06   # mi menor
pad_dawn = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([110, 138.6, 164.8, 220, 277.2, 329.6])) * .055  # lá maior
swell = np.clip((t - 8.55) / 1.3, 0, 1) * (t < 10.45) * .6
pad = pad_night * (1 - dawnmix) * (.7 + swell) + pad_dawn * dawnmix * 1.3
pad *= np.minimum(1, t / 1.0) * np.minimum(1, (DUR - t) / .8)
mus += np.stack([pad, pad * .97], 1)
mus = lp(mus.T, 6000).T

# trilha 6 dB abaixo dos golpes
def peak(x): return np.max(np.abs(x)) + 1e-9
mus *= (peak(fx) * 10 ** (-6 / 20)) / peak(mus) * .8
mixed = fx + mus
mixed /= peak(mixed) * 1.12
out = (np.clip(mixed, -1, 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok', sys.argv[1])
