# Timeline compartilhada + CSS variables

## Arquitetura (cada formato é independente)
```
<campanha>/
  index.html            preview: só os formatos prontos (gerado por `banner.py preview`)
  secoes.txt            opcional: seções do preview ("GCOM: 970x250, 300x250")
  <WxH>/index.html      elementos (1 por linha)
  <WxH>/base.css        reset + easings + keyframes (fixo, não ler)
  <WxH>/timeline.js     bloco TIMELINE (editar) + motor (fixo)
  <WxH>/layout.css      --w, --h, --dist + left/top/width de cada id
  <WxH>/assets/         imagens e SVGs deste formato
```
O master é construído primeiro. `clonar` copia `index.html`, `base.css` e `timeline.js` dele para cada formato (ajustando o tamanho e removendo os ids de `omitir:`), sem tocar em `layout.css` nem em `assets/`. Depois disso cada formato pode ser editado sozinho.

## Passo da timeline
`{ t: 3.6, el: 'f2-txt', anim: 'entra-baixo', dur: 0.6, ease: 'out', rep: 1, loop: false }`
- `ease`: `in`, `out`, `inout` (padrão), `back` (passa do ponto e volta), `linear`.
- `loop: true` faz o passo rodar só quando ainda há outro ciclo. Use para a saída do frame final, assim no último ciclo o CTA fica parado na tela.
- Um elemento sem passos fica visível o tempo todo. Um elemento com entrada fica escondido até ela começar.
- Um passo não pode terminar depois de `duracao` (o check valida).

## Animações (base.css)
- Entradas: `fade-in`, `entra-esq`, `entra-dir`, `entra-cima`, `entra-baixo`, `pop`, `zoom-in`, `zoom-out`, `revela-esq`, `revela-baixo`, `gira-entra`, `ken-burns` (zoom lento de fundo).
- Saídas: `fade-out`, `sai-esq`, `sai-dir`, `sai-cima`, `sai-baixo`.
- Ênfase: `pulso` (use com `rep`), `tremor`.
- Variáveis por formato em layout.css: `--dist`, `--zoom`, `--pulso`, `--borda`, `--fundo`.
- Animação nova: acrescente um `@keyframes` no `base.css` do master (e rode `clonar`) usando só transform, opacity ou clip-path. Se for uma entrada, o nome precisa começar com um dos prefixos de ENTRADA do motor.

## Presets de mood (para sugerir no briefing)
| Mood | Durações | Eases | Animações típicas | Frames |
|---|---|---|---|---|
| Dinâmico / esporte / energia | 0.3–0.5s | out, back | entra-esq/dir, pop, tremor, zoom-in | 2–2.5s |
| Varejo / oferta | 0.4–0.6s | back, out | pop no preço, pulso no CTA (rep 2–3) | 2.5–3s |
| Elegante / premium | 0.8–1.2s | inout | fade, revela-esq, ken-burns no fundo | 3–4s |
| Institucional / informativo | 0.5–0.7s | inout, out | fade, entra-baixo | 3–3.5s |

Regra geral: leitura mínima de ~1s a cada 5 palavras; logo e CTA sempre no frame final; o último ciclo termina parado no frame final.
