"""Render: Playwright (Chrome sem janela) chama renderFrame(i) quadro a quadro (2 subquadros = motion blur),
manda os JPEGs para o ffmpeg (libx264 CRF 16, yuv420p, +faststart) e junta o som masterizado em -14 LUFS / -1,5 dB.
Uso: python render.py short.html som.wav saida.mp4"""
import sys, base64, subprocess, pathlib
from playwright.sync_api import sync_playwright

html, wav, out = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
FPS, DUR = 30, 16
silent = out.replace('.mp4', '_mudo.mp4')
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg',
                       '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                       '-movflags', '+faststart', silent], stdin=subprocess.PIPE)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True); pg = b.new_page(viewport={'width': 720, 'height': 1280})
    pg.goto(html.as_uri()); pg.evaluate('window.ready')
    for i in range(FPS * DUR):
        ff.stdin.write(base64.b64decode(pg.evaluate(f'window.renderFrame({i}, .95)')))
        if i % 60 == 0: print('quadro', i, flush=True)
    b.close()
ff.stdin.close(); ff.wait()
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', silent, '-i', wav, '-map', '0:v', '-map', '1:a',
                '-af', 'acompressor=threshold=0.08:ratio=5:makeup=2:attack=2:release=120,loudnorm=I=-12.6:TP=-2:LRA=11,aresample=48000,alimiter=limit=0.68:level=false:attack=1:release=50', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                '-ar', '48000', '-shortest', '-movflags', '+faststart', out], check=True)
pathlib.Path(silent).unlink()
print('ok', out)
