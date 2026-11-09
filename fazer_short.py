"""Faz o Short do martelo a partir da ficha.txt (a FICHA DO SHORT que o ChatGPT gerou).
Uso:  python fazer_short.py            → lê ficha.txt e cria meu_short.mp4 + folha_de_contato.jpg
      python fazer_short.py outra.txt saida.mp4
Precisa: Python 3.10+, ffmpeg no PATH e  pip install numpy scipy playwright  +  python -m playwright install chromium
"""
import json, re, subprocess, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = pathlib.Path(__file__).resolve().parent
ficha = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else AQUI / 'ficha.txt')
saida = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else AQUI / 'meu_short.mp4').resolve()
txt = ficha.read_text(encoding='utf-8')

def campo(rotulo):
    m = re.search(rf'^\s*{rotulo}[^:\n]*:\s*(.+?)\s*$', txt, re.M | re.I)
    if not m: sys.exit(f'ERRO: não achei "{rotulo}" na ficha. Confira a ficha.txt.')
    return m.group(1).strip().strip('"“”')

muros = [campo(f'Muro {i}').upper() for i in range(1, 5)]
bandeira = campo('Bandeira').upper()
legendas = []
for i in range(1, 4):
    partes = [p.strip() for p in campo(f'Legenda {i}').split('/')]
    if len(partes) != 2: sys.exit(f'ERRO: a Legenda {i} precisa ter duas linhas separadas por " / ".')
    legendas.append(partes)
for w in muros + [bandeira]:
    if len(w) > 22: print(f'AVISO: "{w}" é longo; vai ficar com letra pequena no muro.')
for a, b in legendas:
    if max(len(a), len(b)) > 26: print(f'AVISO: legenda "{a} / {b}" passa de 26 letras numa linha e pode sair da tela.')

dados = {'muros': muros, 'bandeira': bandeira, 'legendas': legendas}
(AQUI / 'ficha.js').write_text('window.FICHA = ' + json.dumps(dados, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
print('ficha.js atualizado:', json.dumps(dados, ensure_ascii=False))

py = sys.executable
print('1/3 criando os sons…', flush=True)
subprocess.run([py, str(AQUI / 'sons.py'), str(AQUI / 'som.wav')], check=True)
print('2/3 desenhando os 480 quadros e codificando o vídeo…', flush=True)
subprocess.run([py, str(AQUI / 'render.py'), str(AQUI / 'short.html'), str(AQUI / 'som.wav'), str(saida)], check=True)
print('3/3 folha de contato (2 quadros por segundo)…', flush=True)
folha = saida.with_name('folha_de_contato.jpg')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(saida), '-vf', 'fps=2,scale=180:320,tile=8x4',
                '-frames:v', '1', str(folha)], check=True)
print(f'PRONTO: {saida}\nFolha de contato: {folha}  ← abra e confira os muros, as legendas e a bandeira.')
