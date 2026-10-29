# Ler o Figma gastando pouco

## Link por nó
No Figma: selecione o frame (ou a Section que agrupa os frames) → botão direito → **Copy/Paste as → Copy link to selection**.
URL: `figma.com/design/<fileKey>/Nome?node-id=12-345` → fileKey = `<fileKey>`, nodeId = `12:345` (troque `-` por `:`).

## Ordem de leitura (da mais barata para a mais cara)
1. `create_session` com o fileKey (obrigatório antes das outras ferramentas do Figma).
2. `get_metadata` no node da Section ou da página: devolve um XML enxuto com ids, nomes, x/y/width/height de todos os frames e filhos. É daqui que saem os valores do layout.css. As posições dos filhos são relativas ao frame pai.
3. `get_screenshot` **só** nos frames do master, para entender a campanha e sugerir animações.
4. `get_design_context` só se faltar algo (cor, fonte, texto), e sempre num node pequeno, nunca na página.
5. Assets: o mais barato é o usuário exportar do Figma direto para `<campanha>/_figma/<formato>/` com os nomes certos. Se não der, use `download_assets` nos nodes específicos.

## Sem Figma (prints)
Peça um print por frame, recortado no tamanho exato do formato e com zoom de 100%. Meça as posições pelo print e peça os assets exportados.
