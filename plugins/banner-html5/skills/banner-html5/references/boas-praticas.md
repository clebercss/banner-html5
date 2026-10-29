# Boas práticas (já embutidas no template)

- `<meta name="ad.size" content="width=W,height=H">` e `var clickTag` no `<head>`. O clique usa `window.open(window.clickTag)`, nunca uma URL fixa.
- `index.html` fica na raiz do zip. Nenhuma requisição externa (exceto libs do ad server, como s0.2mdn.net).
- Posicionamento absoluto com left/top/width em px; transform, opacity e clip-path ficam só para a animação (GPU, sem reflow).
- O banner fica oculto até o `load` (classe `.pronto`), sem flash de imagens carregando.
- Borda de 1px (`--borda`), porque muitos veículos exigem. Se não for o caso, use `--borda: transparent`.
- Texto como SVG/PNG (sem webfont). Use fonte do sistema só se o layout permitir.
- Imagens: JPG para fotos, SVG para vetores, PNG para transparência complexa. Sem assets não usados (o check acusa).
- `alt` vazio em imagens decorativas; `aria-label` no `#banner` com a mensagem principal.
- Sem `console.log`, sem bibliotecas pesadas. O motor CSS + JS próprio pesa menos de 2KB.
- Backup estático (JPG do frame final no tamanho do formato): gere se o veículo pedir, fora da pasta do formato.
- Antes de entregar: `check` sem erros, preview revisado, zip gerado pelo script.
