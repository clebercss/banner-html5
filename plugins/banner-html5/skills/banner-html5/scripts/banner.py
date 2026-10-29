#!/usr/bin/env python3
"""banner.py — utilitário da skill banner-html5. Saída curta de propósito (economia de tokens).

Cada formato é independente: tem o próprio index.html, base.css, timeline.js, layout.css e assets/.

  python banner.py novo     <campanha> <formatos...>            cria as pastas dos formatos a partir do template
  python banner.py clonar   <campanha> <master> [formatos...]   copia index.html/base.css/timeline.js do master
                                                               (nunca mexe em layout.css nem assets/)
  python banner.py otimizar <campanha> [formatos...] [--q 85]   comprime assets (originais em _originais/)
  python banner.py check    <campanha> [formatos...] [--raw]    valida peso, duração, clickTag e assets
  python banner.py zip      <campanha> [formatos...]            gera _entrega/<campanha>_<formato>.zip (só os OK)
  python banner.py preview  <campanha>                          gera <campanha>/index.html só com os formatos prontos
  python banner.py setup                                        confere e instala o que faltar (Pillow, svgo)

Grupos: todos, g200, g150, g50, g60. Sem formatos = todas as pastas WxH da campanha.
Formatos aceitam texto livre ("300 x 250, 728X90"), variações (480x320v1) e formatos novos
com limites: 300x600:150:30 (KB:segundos).
Preview: se existir <campanha>/secoes.txt ("GCOM: 970x250, 300x250" por linha), agrupa por seção.
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
# ordem do index de preview
ORDEM = ['970x250', '970x150', '970x90', '320x50', '300x250', '1248x250', '480x320', '320x480',
         '728x90', '468x60', '120x60', '90x60', '160x600', '120x600']
CODIGO = {'index.html', 'base.css', 'layout.css', 'timeline.js'}
CDN_OK = ('s0.2mdn.net',)  # bibliotecas servidas pelo ad server (não contam peso)
RE_FMT = re.compile(r'^\d+x\d+(v\d+)?$')
EXTRA = 'formatos_extra.txt'  # formatos fora da tabela, por campanha: "WxH KB segundos"


def sair(msg):
    print('ERRO: ' + msg)
    sys.exit(1)


def base(fmt):
    """'480x320v2' -> '480x320'"""
    return re.match(r'\d+x\d+', fmt).group()


def wh(fmt):
    return base(fmt).split('x')


def limites(fmt):
    return FORMATOS[base(fmt)]


def carregar_extras(camp):
    for linha in (camp / EXTRA).read_text(encoding='utf-8').splitlines() if (camp / EXTRA).exists() else []:
        f, kb, s = linha.split()
        FORMATOS[f] = (int(kb), int(s))


def tokens(nomes):
    """Aceita formatos digitados livremente: '300 x 250, 728X90 320×50' -> ['300x250', '728x90', '320x50']."""
    txt = re.sub(r'(\d)\s*[xX×]\s*(\d)', r'\1x\2', ' '.join(nomes))
    return [t for t in re.split(r'[,;\s]+', txt) if t]


def pastas(camp):
    return sorted(p.name for p in camp.iterdir() if p.is_dir() and RE_FMT.match(p.name))


def formatos(camp, nomes, criar=False):
    if not nomes:
        return pastas(camp) or sair('nenhuma pasta de formato em ' + str(camp))
    lista = []
    for n in tokens(nomes):
        m = re.match(r'^(\d+x\d+):(\d+):(\d+)$', n)  # formato novo com limites: 300x600:150:30
        if m:
            n = m.group(1)
            FORMATOS[n] = (int(m.group(2)), int(m.group(3)))
            with open(camp / EXTRA, 'a', encoding='utf-8') as arq:
                arq.write(f'{n} {m.group(2)} {m.group(3)}\n')
        for f in GRUPOS.get(n, [n]):
            if not RE_FMT.match(f) or base(f) not in FORMATOS:
                sair(f'formato fora da tabela: {f} (informe os limites assim: {base(f) if RE_FMT.match(f) else f}:KB:segundos)')
            if not criar and not (camp / f).is_dir():
                sair(f'pasta inexistente: {f}')
            if f not in lista:
                lista.append(f)
    return lista


# ---------- novo / clonar ----------

def cmd_novo(camp, nomes):
    fmts = formatos(camp, nomes, criar=True)
    criados = []
    for f in fmts:
        pasta = camp / f
        (pasta / 'assets').mkdir(parents=True, exist_ok=True)
        w, h = wh(f)
        for arq in ('index.html', 'base.css', 'timeline.js', 'layout.css'):
            if not (pasta / arq).exists():
                txt = (TEMPLATE / 'formato' / arq).read_text(encoding='utf-8')
                (pasta / arq).write_text(txt.replace('{{W}}', w).replace('{{H}}', h), encoding='utf-8')
        criados.append(f)
    print('criado: ' + ', '.join(criados))


def omitidos(layout):
    m = re.search(r'omitir:([^\n*]*)', layout)
    return [i.lstrip('#') for i in re.split(r'[\s,]+', m.group(1)) if i] if m else []


def cmd_clonar(camp, master, nomes):
    if not (camp / master / 'index.html').exists():
        sair('master sem index.html: ' + master)
    mw, mh = wh(master)
    html_m = (camp / master / 'index.html').read_text(encoding='utf-8')
    alvos = [f for f in formatos(camp, nomes, criar=True) if f != master] if nomes else \
        [f for f in pastas(camp) if f != master]
    saida = []
    for f in alvos:
        pasta = camp / f
        (pasta / 'assets').mkdir(parents=True, exist_ok=True)
        w, h = wh(f)
        html = re.sub(rf'width={mw},height={mh}', f'width={w},height={h}', html_m)
        html = re.sub(rf'(<title>[^<]*?){mw}x{mh}', rf'\g<1>{w}x{h}', html)
        lay = pasta / 'layout.css'
        if not lay.exists():
            lay.write_text((TEMPLATE / 'formato' / 'layout.css').read_text(encoding='utf-8')
                           .replace('{{W}}', w).replace('{{H}}', h), encoding='utf-8')
        omit = omitidos(lay.read_text(encoding='utf-8'))
        for i in omit:
            html = re.sub(r'^[ \t]*<[^\n]*\bid="' + re.escape(i) + r'"[^\n]*\n', '', html, flags=re.M)
        (pasta / 'index.html').write_text(html, encoding='utf-8')
        for arq in ('base.css', 'timeline.js'):
            shutil.copy2(camp / master / arq, pasta / arq)
        saida.append(f + (f' (omitidos: {", ".join(omit)})' if omit else ''))
    print(f'clonado de {master}: ' + (', '.join(saida) or 'nenhum'))


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
    peso_max, dur_max = limites(f)
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
            elif pasta.resolve() not in alvo.parents:
                erros.append(f'arquivo fora da pasta do formato: {r}')
    for a in (pasta / 'assets').glob('*'):
        if a.is_file() and a.resolve() not in usados:
            avisos.append(f'asset não usado (pesa à toa): {a.name}')
    for a in pasta.iterdir():
        if a.is_file() and a.name not in CODIGO:
            avisos.append(f'arquivo extra na raiz: {a.name}')
    if not pronto(pasta):
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
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        for passo in re.findall(r'\{[^{}]*\bt:[^{}]*\}', js):
            num = lambda k, pad: float((re.search(k + r':\s*([\d.]+)', passo) or [None, pad])[1])
            el = re.search(r"el:\s*'([^']+)'", passo)
            fim = num('t', 0) + num('dur', 0) * num('rep', 1)
            if fim > d + 0.01:
                erros.append(f'passo termina em {fim:g}s, depois da duracao ({d:g}s)')
            if el and el.group(1) not in ids and el.group(1) not in omitidos(ler(pasta / 'layout.css')):
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


def pronto(pasta):
    """Formato construído: tem index.html, layout preenchido e assets."""
    return ((pasta / 'index.html').exists() and any((pasta / 'assets').glob('*'))
            and not re.search(r':\s*0px;\s*}', ler(pasta / 'layout.css')))


def ordenar(fmts):
    chave = lambda f: (ORDEM.index(base(f)) if base(f) in ORDEM else len(ORDEM), f)
    return sorted(fmts, key=chave)


def cmd_preview(camp):
    prontos = [f for f in pastas(camp) if pronto(camp / f)]
    secoes = []
    if (camp / 'secoes.txt').exists():
        for linha in ler(camp / 'secoes.txt').splitlines():
            if ':' in linha:
                nome, fs = linha.split(':', 1)
                secoes.append((nome.strip(), [f for f in tokens([fs]) if f in prontos]))
    else:
        secoes.append((camp.name.upper(), ordenar(prontos)))
    modelo = ler(TEMPLATE / 'preview.html')
    secao_tpl = re.search(r'<!--SECAO-->(.*?)<!--/SECAO-->', modelo, re.S).group(1)
    fmt_tpl = re.search(r'<!--FORMATO-->(.*?)<!--/FORMATO-->', modelo, re.S).group(1)
    blocos = []
    for nome, fs in secoes:
        for i, f in enumerate(fs):
            w, h = wh(f)
            titulo = secao_tpl.replace('{{SECAO}}', nome) if i == 0 else ''
            blocos.append(fmt_tpl.replace('{{TITULO_SECAO}}', titulo)
                          .replace('{{F}}', f).replace('{{W}}', w).replace('{{H}}', h))
    html = re.sub(r'<!--SECAO-->.*?<!--/SECAO-->\s*', '', modelo, flags=re.S)
    html = re.sub(r'<!--FORMATO-->.*?<!--/FORMATO-->', lambda m: ''.join(blocos), html, flags=re.S)
    (camp / 'index.html').write_text(html.replace('{{CAMPANHA}}', camp.name.upper()), encoding='utf-8')
    total = sum(len(fs) for _, fs in secoes)
    print(f'preview: index.html com {total} formato(s) pronto(s): ' + ', '.join(dict.fromkeys(f for _, fs in secoes for f in fs)))


def cmd_setup():
    """Instala só o que falta. Rápido quando já está tudo instalado."""
    st = []
    try:
        import PIL  # noqa: F401
        st.append('pillow OK')
    except ImportError:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'pillow'], capture_output=True, text=True)
        st.append('pillow instalado' if r.returncode == 0 else 'pillow FALHOU (rode: python -m pip install pillow)')
    if shutil.which('svgo'):
        st.append('svgo OK')
    elif shutil.which('npm'):
        r = subprocess.run([shutil.which('npm'), 'i', '-g', 'svgo'], capture_output=True, text=True)
        st.append('svgo instalado' if r.returncode == 0 else 'svgo FALHOU (rode: npm i -g svgo)')
    else:
        st.append('svgo ausente: instale o Node.js (nodejs.org) e rode npm i -g svgo')
    if not shutil.which('pngquant'):
        st.append('pngquant opcional ausente (pngquant.org)')
    print('setup: ' + ' | '.join(st))


def main(argv):
    if argv[:1] == ['setup']:
        return cmd_setup()
    if len(argv) < 2 or argv[0] not in ('novo', 'clonar', 'otimizar', 'check', 'zip', 'preview'):
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
    if camp.is_dir():
        carregar_extras(camp)
    if cmd == 'novo':
        camp.mkdir(parents=True, exist_ok=True)
        cmd_novo(camp, nomes)
    elif not camp.is_dir():
        sair('campanha inexistente: ' + str(camp))
    elif cmd == 'clonar':
        if not nomes:
            sair('informe o master: clonar <campanha> <master> [formatos...]')
        cmd_clonar(camp, tokens(nomes[:1])[0], nomes[1:])
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
