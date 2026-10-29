# Formatos

| Formato | Peso máx. | Duração máx. | Grupo |
|---|---|---|---|
| 1248x250 | 200KB | 15s | g200 |
| 970x250, 970x150, 970x90, 320x480, 480x320 | 150KB | 30s | g150 |
| 320x50 | 50KB | 30s | g50 |
| 160x600, 120x600, 468x60, 120x60, 90x60, 728x90, 300x250 | 60KB | 30s | g60 |

- 1 KB = 1000 bytes (conservador). O critério padrão é o tamanho do .zip; use `check --raw` se a veiculação medir pela soma dos arquivos.
- A duração é o tempo total contando os loops. O motor calcula `ciclos = min(loops, floor(limite / duracao))`, então a mesma timeline serve para o 1248x250 (15s) e para os demais (30s).
- O ciclo nunca pode passar do limite do formato: o `check` acusa erro.

## --dist sugerido (deslocamento das entradas)
| Tipo | Formatos | --dist |
|---|---|---|
| Grande | 1248x250, 970x250, 320x480, 480x320, 300x250 | 40px |
| Faixa/torre | 970x150, 970x90, 728x90, 160x600, 120x600, 468x60 | 24px |
| Mini | 320x50, 120x60, 90x60 | 12px |

## Resolução dos assets
- 60KB/50KB: exportar em 1x. Fotos em JPG; texto, logo e CTA em SVG (ou PNG-8 se o SVG ficar pesado).
- 150KB/200KB: dá para usar 1.5x ou 2x em fotos se o `check` mostrar folga. Sempre exporte primeiro em 1x.
