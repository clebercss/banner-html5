#!/usr/bin/env python3
"""banner.py — utilitário da skill banner-html5. Saída curta de propósito (economia de tokens).

  python banner.py novo     <campanha> <formatos|grupos...>  cria _shared/ e as pastas dos formatos
  python banner.py sync     <campanha> [formatos...]         gera index.html e copia base.css/timeline.js
  python banner.py otimizar <campanha> [formatos...] [--q 85] comprime assets (originais em _originais/)
  python banner.py check    <campanha> [formatos...] [--raw] valida peso, duração, clickTag e assets
  python banner.py zip      <campanha> [formatos...]         gera _entrega/<campanha>_<formato>.zip (só os OK)
  python banner.py preview  <campanha>                       gera _preview.html com todos os formatos

Grupos: todos, g200, g150, g50, g60. Sem formatos = todas as pastas WxH da campanha.
Peso: 1 KB = 1000 bytes (conservador). Critério padrão: tamanho do .zip; --raw usa a soma dos arquivos.
"""
import io
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TEMPLATE = AQUI.parent / 'templates'
KB = 1000

# formato: (peso máximo em KB, duração máxima em s)
FORMATOS = {
    '1248x250': (200, 15),
    '970x250': (150, 30), '970x150': (150, 30), '970x90': (150, 30), '320x480': (150, 30), '480x320': (150, 30),
    '320x50': (50, 30),
    '160x600': (60, 30), '120x600': (60, 30), '468x60': (60, 30), '120x60': (60, 30),
    '90x60': (60, 30), '728x90': (60, 30), '300x250': (60, 30),
}
GRUPOS = {
    'g200': ['1248x250'],
    'g150': ['970x250', '970x150', '970x90', '320x480', '480x320'],
    'g50': ['320x50'],
    'g60': ['160x600', '120x600', '468x60', '120x60', '90x60', '728x90', '300x250'],
}
GRUPOS['todos'] = [f for g in GRUPOS.values() for f in g]
CODIGO = {'index.html', 'base.css', 'layout.css', 'timeline.js'}
CDN_OK = ('s0.2mdn.net',)  # bibliotecas servidas pelo ad server (não contam peso)
RE_FMT = re.compile(r'^\d+x\d+$')


def sair(msg):
    print('ERRO: ' + msg)
    sys.exit(1)


def formatos(camp, nomes, criar=False):
    if not nomes:
        achados = sorted(p.name for p in camp.iterdir() if p.is_dir() and RE_FMT.match(p.name))
        return achados or sair('nenhuma pasta de formato em ' + str(camp))
    lista = []
    for n in nomes:
        for f in GRUPOS.get(n, [n]):
            if f not in FORMATOS:
                sair(f'formato fora da tabela: {f}')
            if not criar and not (camp / f).is_dir():
                sair(f'pasta inexistente: {f}')
            if f not in lista:
                lista.append(f)
    return lista


def wh(fmt):
    return fmt.split('x')


# ---------- novo / sync ----------

def cmd_novo(camp, nomes):
    fmts = formatos(camp, nomes, criar=True)
    shared = camp / '_shared'
    if not shared.exists():
        shutil.copytree(TEMPLATE / '_shared', shared)
    modelo = (TEMPLATE / 'layout.css').read_text(encoding='utf-8')
    for f in fmts:
        w, h = wh(f)
        (camp / f / 'assets').mkdir(parents=True, exist_ok=True)
        lay = camp / f / 'layout.css'
        if not lay.exists():
            lay.write_text(modelo.replace('{{W}}', w).replace('{{H}}', h), encoding='utf-8')
    print('criado: ' + ', '.join(fmts))
    cmd_sync(camp, fmts)


def omitidos(layout):
    m = re.search(r'omitir:([^\n*]*)', layout)
    return [i.lstrip('#') for i in re.split(r'[\s,]+', m.group(1)) if i] if m else []


def cmd_sync(camp, nomes):
    shared = camp / '_shared'
    if not shared.is_dir():
        sair('sem _shared/ — rode "novo" primeiro')
    base = (shared / 'index.html').read_text(encoding='utf-8')
    saida = []
    for f in formatos(camp, nomes):
        w, h = wh(f)
        lay = camp / f / 'layout.css'
        omit = omitidos(lay.read_text(encoding='utf-8')) if lay.exists() else []
        html = base.replace('{{W}}', w).replace('{{H}}', h)
        for i in omit:
            html = re.sub(r'^[ \t]*<[^\n]*\bid="' + re.escape(i) + r'"[^\n]*\n', '', html, flags=re.M)
        (camp / f / 'index.html').write_text(html, encoding='utf-8')
        for arq in ('base.css', 'timeline.js'):
            shutil.copy2(shared / arq, camp / f / arq)
        saida.append(f + (f' (omitidos: {", ".join(omit)})' if omit else ''))
    print('sync: ' + ', '.join(saida))


# ---------- otimizar ----------

def minify_svg(txt):
    txt = re.sub(r'<\?xml[^>]*\?>|<!--.*?-->|<metadata.*?</metadata>|<sodipodi:[^>]*?/>', '', txt, flags=re.S)
    txt = re.sub(r'\s(?:inkscape|sodipodi):[\w-]+="[^"]*"|\sxmlns:(?:inkscape|sodipodi)="[^"]*"', '', txt)
    txt = re.sub(r'>\s*\n\s*<', '><', txt)
    return txt.strip()


def otimizar_arquivo(src, dst, q, ferr):
    ext = src.suffix.lower()
    tmp = dst.with_name(dst.name + '.tmp')
    try:
        if ext == '.png' and ferr['pngquant']:
            r = subprocess.run([ferr['pngquant'], '--quality=70-95', '--speed', '1', '--strip', '--force',
                                '--output', str(tmp), str(src)], capture_output=True)
            if r.returncode != 0:
                shutil.copy2(src, tmp)
            if ferr['oxipng']:
                subprocess.run([ferr['oxipng'], '-o', '4', '--strip', 'safe', '-q', str(tmp)], capture_output=True)
        elif ext == '.png' and ferr['pil']:
            ferr['pil'].open(src).save(tmp, 'PNG', optimize=True)
        elif ext in ('.jpg', '.jpeg') and ferr['pil']:
            ferr['pil'].open(src).convert('RGB').save(tmp, 'JPEG', quality=q, optimize=True, progressive=True)
        elif ext == '.svg' and ferr['svgo']:
            subprocess.run([ferr['svgo'], '-i', str(src), '-o', str(tmp), '--multipass', '-q'], capture_output=True)
        elif ext == '.svg':
            tmp.write_text(minify_svg(src.read_text(encoding='utf-8')), encoding='utf-8')
        else:
            shutil.copy2(src, dst)
            return
        if not tmp.exists() or tmp.stat().st_size >= src.stat().st_size:
            shutil.copy2(src, dst)  # não compensou: mantém o original
        else:
            shutil.copy2(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()


def cmd_otimizar(camp, nomes, q):
    try:
        from PIL import Image as pil
    except ImportError:
        pil = None
    ferr = {'pngquant': shutil.which('pngquant'), 'oxipng': shutil.which('oxipng'),
            'svgo': shutil.which('svgo'), 'pil': pil}
    for f in formatos(camp, nomes):
        orig = camp / '_originais' / f
        antes = depois = 0
        for a in sorted((camp / f / 'assets').glob('*')):
            if not a.is_file():
                continue
            bkp = orig / a.name
            if not bkp.exists() or bkp.stat().st_mtime < a.stat().st_mtime - 1:
                orig.mkdir(parents=True, exist_ok=True)
                shutil.copy2(a, bkp)  # sempre comprime a partir do original (sem perda acumulada)
            antes += bkp.stat().st_size
            otimizar_arquivo(bkp, a, q, ferr)
            depois += a.stat().st_size
        print(f'{f}: assets {antes / KB:.1f}KB -> {depois / KB:.1f}KB')
    falta = []
    if not ferr['pngquant'] and not pil:
        falta.append('PNG: instale pngquant ou "pip install pillow"')
    if not pil:
        falta.append('JPG: "pip install pillow"')
    if not ferr['svgo']:
        falta.append('SVG: minificação básica (svgo dá mais ganho: "npm i -g svgo")')
    if falta:
        print('aviso: ' + ' | '.join(falta))


# ---------- check ----------

def tamanhos(pasta):
    arqs = [p for p in pasta.rglob('*') if p.is_file()]
    raw = sum(p.stat().st_size for p in arqs)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in arqs:
            z.write(p, p.relative_to(pasta).as_posix())
    return raw, len(buf.getvalue())


def ler(p):
    return p.read_text(encoding='utf-8') if p.exists() else ''


def checar(camp, f, usar_raw):
    peso_max, dur_max = FORMATOS[f]
    pasta = camp / f
    erros, avisos = [], []
    html = ler(pasta / 'index.html')
    if not html:
        return False, f'ERRO {f}: sem index.html', []
    css = ler(pasta / 'base.css') + ler(pasta / 'layout.css')
    js = ler(pasta / 'timeline.js')
    w, h = wh(f)

    if not re.search(rf'name="ad\.size"\s+content="width={w},height={h}"', html):
        erros.append('meta ad.size ausente ou diferente do formato')
    if not re.search(r'clickTag\s*=', html):
        erros.append('clickTag não definido')
    if re.search(r'<svg[\s>]', html):
        avisos.append('SVG inline no HTML (regra: assets em assets/, só inline se estourar peso)')

    refs = re.findall(r'(?:src|href)="([^"]+)"', html) + re.findall(r'url\(\s*[\'"]?([^\'")]+)', css)
    usados = set()
    for r in refs:
        if r.startswith('data:'):
            avisos.append('data: URI embutido (regra: assets em assets/)')
        elif r.startswith(('http:', 'https:', '//')):
            if not any(c in r for c in CDN_OK):
                erros.append(f'requisição externa: {r}')
        elif not r.startswith(('javascript:', '#')):
            alvo = (pasta / r).resolve()
            usados.add(alvo)
            if not alvo.exists():
                erros.append(f'arquivo não encontrado: {r}')
    for a in (pasta / 'assets').glob('*'):
        if a.is_file() and a.resolve() not in usados:
            avisos.append(f'asset não usado (pesa à toa): {a.name}')
    for a in pasta.iterdir():
        if a.is_file() and a.name not in CODIGO:
            avisos.append(f'arquivo extra na raiz: {a.name}')
    if re.search(r':\s*0px;\s*}', ler(pasta / 'layout.css')):
        avisos.append('layout.css com width 0px (posições não preenchidas?)')

    dur = re.search(r'duracao:\s*([\d.]+)', js)
    loops = re.search(r'loops:\s*(\d+)', js)
    tempo = '?'
    if not dur:
        erros.append('timeline.js sem "duracao"')
    else:
        d = float(dur.group(1))
        n = max(1, min(int(loops.group(1)) if loops else 1, int(dur_max // d) if d else 1))
        tempo = f'{d:g}s x{n}={d * n:g}s/{dur_max}s'
        if d > dur_max:
            erros.append(f'ciclo de {d:g}s passa do máximo de {dur_max}s')
        ids_shared = set(re.findall(r'\bid="([^"]+)"', ler(camp / '_shared' / 'index.html')))
        for passo in re.findall(r'\{[^{}]*\bt:[^{}]*\}', js):
            num = lambda k, pad: float((re.search(k + r':\s*([\d.]+)', passo) or [None, pad])[1])
            el = re.search(r"el:\s*'([^']+)'", passo)
            fim = num('t', 0) + num('dur', 0) * num('rep', 1)
            if fim > d + 0.01:
                erros.append(f'passo termina em {fim:g}s, depois da duracao ({d:g}s)')
            if el and ids_shared and el.group(1) not in ids_shared:
                avisos.append(f'passo aponta para #{el.group(1)} inexistente')

    raw, zp = tamanhos(pasta)
    peso = raw if usar_raw else zp
    if peso > peso_max * KB:
        erros.append(f'peso {peso / KB:.1f}KB acima de {peso_max}KB')
    elif peso > peso_max * KB * 0.95:
        avisos.append('peso acima de 95% do limite')
    status = 'OK  ' if not erros else 'ERRO'
    linha = (f'{status} {f:<9} {peso / KB:6.1f}/{peso_max}KB {"raw" if usar_raw else "zip"} '
             f'(raw {raw / KB:.1f})  {tempo}')
    return not erros, linha, ['  x ' + e for e in erros] + ['  ! ' + a for a in dict.fromkeys(avisos)]


def cmd_check(camp, nomes, usar_raw):
    fmts = formatos(camp, nomes)
    ok_total = 0
    for f in fmts:
        ok, linha, det = checar(camp, f, usar_raw)
        ok_total += ok
        print(linha)
        for d in det:
            print(d)
    print(f'{ok_total}/{len(fmts)} OK')
    return ok_total == len(fmts)


# ---------- zip / preview ----------

def cmd_zip(camp, nomes):
    dest = camp / '_entrega'
    dest.mkdir(exist_ok=True)
    for f in formatos(camp, nomes):
        ok, _, _ = checar(camp, f, False)
        if not ok:
            print(f'{f}: pulado (rode check)')
            continue
        z = dest / f'{camp.name}_{f}.zip'
        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for p in sorted((camp / f).rglob('*')):
                if p.is_file():
                    zf.write(p, p.relative_to(camp / f).as_posix())
        print(f'{f}: {z.name} {z.stat().st_size / KB:.1f}KB')


def cmd_preview(camp):
    cards = ''.join(
        f'<figure><figcaption>{f}</figcaption>'
        f'<iframe src="{f}/index.html" width="{wh(f)[0]}" height="{wh(f)[1]}" scrolling="no"></iframe></figure>'
        for f in formatos(camp, []))
    (camp / '_preview.html').write_text(
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><title>Preview</title><style>'
        'body{font:14px system-ui;background:#eee;margin:16px}figure{display:inline-block;vertical-align:top;'
        'margin:0 16px 16px 0}figcaption{margin-bottom:4px;color:#555}iframe{border:0;background:#fff;display:block}'
        'button{margin-bottom:16px;padding:6px 14px}</style></head><body>'
        '<button onclick="document.querySelectorAll(\'iframe\').forEach(function(i){i.src=i.src})">Reiniciar</button><br>'
        + cards + '</body></html>', encoding='utf-8')
    print('preview: ' + str(camp / '_preview.html'))


def main(argv):
    if len(argv) < 2 or argv[0] not in ('novo', 'sync', 'otimizar', 'check', 'zip', 'preview'):
        print(__doc__)
        sys.exit(1)
    cmd, camp, resto = argv[0], Path(argv[1]).expanduser().resolve(), argv[2:]
    usar_raw = '--raw' in resto
    q = 85
    if '--q' in resto:
        i = resto.index('--q')
        q = int(resto[i + 1])
        del resto[i:i + 2]
    nomes = [r for r in resto if not r.startswith('--')]
    if cmd == 'novo':
        camp.mkdir(parents=True, exist_ok=True)
        cmd_novo(camp, nomes)
    elif not camp.is_dir():
        sair('campanha inexistente: ' + str(camp))
    elif cmd == 'sync':
        cmd_sync(camp, nomes)
    elif cmd == 'otimizar':
        cmd_otimizar(camp, nomes, q)
    elif cmd == 'check':
        sys.exit(0 if cmd_check(camp, nomes, usar_raw) else 1)
    elif cmd == 'zip':
        cmd_zip(camp, nomes)
    elif cmd == 'preview':
        cmd_preview(camp)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1:])
