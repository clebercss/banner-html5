---
name: banner-html5
description: Cria banners HTML5 animados (mídia display) a partir de frames do Figma ou prints, nos formatos 1248x250, 970x250, 970x150, 970x90, 320x480, 480x320, 320x50, 160x600, 120x600, 468x60, 120x60, 90x60, 728x90 e 300x250, respeitando limites de peso (KB) e duração. Use quando o usuário pedir banner animado, "animado" HTML5, peça display ou chamar /banner-html5.
argument-hint: "[link do Figma (com node-id) ou card]"
---

# Banner HTML5

Ferramenta: `B="python <dir>/scripts/banner.py"`, em que `<dir>` é o diretório base desta skill (informado quando ela é carregada). Use caminho absoluto e rode pelo Bash. A saída já é resumida, então não releia os arquivos para conferir o que o script já reportou.

## Regras fixas
- Peso e duração por formato: `references/formatos.md`. O script `check` é a fonte da verdade.
- Siga os frames enviados à risca: posições, tamanhos e proporções exatas em px.
- Todo elemento visual fica em `<formato>/assets/` como arquivo separado, **inclusive SVG**. Só vale inline/data URI se o formato continuar acima do peso depois do `otimizar`, e nesse caso avise o usuário.
- Arquitetura (não mude): `_shared/` tem `index.html`, `base.css` e `timeline.js`, iguais em todos os formatos. Cada formato tem só `layout.css` e `assets/`. Detalhes em `references/timeline.md`.

## 0. Pasta de destino (obrigatório, antes de qualquer arquivo)
Toda campanha precisa ser salva numa pasta local escolhida pelo usuário. Nunca salve numa pasta temporária ou de sessão.
- Se a ferramenta `request_directory` existir, chame-a **sem path** (ela abre o seletor de pastas) e depois `change_directory` com a pasta devolvida. Até o fim do turno, use o caminho absoluto.
- Se ela não existir, pergunte o caminho da pasta na mesma mensagem em que pedir o link.
- Se a sessão já estiver numa pasta escolhida pelo usuário para esta campanha, use essa pasta e não pergunte de novo.
- A campanha fica em `<pasta>/<nome-curto>/` (por exemplo `cabore`). No Windows, prefira caminhos curtos (limite de 260 caracteres).

## 1. Briefing (no máximo 2 rodadas)
1. Se o link ou o card não veio no argumento, peça **só isso**, em uma linha, lembrando o usuário de enviar o link com `node-id` (ver `references/figma.md`).
2. Leia a campanha da forma mais barata (`references/figma.md`) e faça **uma única** chamada AskUserQuestion com 4 perguntas:
   - **Formatos** (multiSelect): `1248x250`, `Grupo 150KB` (970x250, 970x150, 970x90, 320x480, 480x320), `320x50`, `Grupo 60KB` (160x600, 120x600, 468x60, 120x60, 90x60, 728x90, 300x250). Em "Other", o usuário digita uma lista avulsa.
   - **Mood**: 3 opções deduzidas da campanha (presets em `references/timeline.md`).
   - **Animações por frame**: 2 ou 3 propostas concretas baseadas na campanha (ex.: "F1 texto entra-esq out 0.5s · F2 produto pop back · CTA pulso"), com a primeira marcada como (Recomendado).
   - **Observações**: "Nenhuma" / "Tenho observações" (o usuário escreve em Other).

## 2. Master
1. Escolha como master o formato com mais elementos e frames detalhados (de preferência o 300x250, se estiver na lista).
2. `$B novo <campanha> <formatos/grupos>` cria a estrutura de todos os formatos de uma vez.
3. Coloque os assets do master em `<master>/assets/`, usando os mesmos nomes de arquivo que valerão para todos os formatos.
4. Edite `_shared/index.html`: um `<img class="el">` por linha, com ids que descrevem o elemento (`f1-titulo`, `produto`, `cta`).
5. Edite `_shared/timeline.js` (só o bloco TIMELINE) e o `layout.css` do master.
6. Rode `$B sync <campanha>`, depois `$B otimizar <campanha> <master>`, depois `$B check <campanha> <master>`.
7. Rode `$B preview <campanha>` e peça a aprovação do master antes de adaptar os outros formatos.

## 3. Adaptação dos outros formatos → subagente `banner-adaptador`
Delegue **uma única** chamada Agent (`subagent_type: banner-html5:banner-adaptador`) para todos os formatos restantes. Se forem mais de 7 formatos, divida em 2 chamadas paralelas. O subagente já roda em Sonnet com esforço baixo. O prompt deve ser curto e conter só:
- o comando `B` completo, com o caminho absoluto do banner.py;
- caminho da campanha e formato master;
- lista de formatos alvo, cada um com sua fonte de layout (fileKey + node-id do frame, ou caminho do print);
- de onde vêm os assets (pasta exportada pelo usuário ou "baixar via Figma");
- elementos que não existem em algum formato (ele marca `omitir:`).

Não repasse o briefing inteiro: o subagente não mexe na timeline. Confira apenas o resumo que ele devolver.

## 4. Entrega
`$B check <campanha>` → `$B zip <campanha>` → `$B preview <campanha>`. Informe ao usuário a tabela do check e a pasta `_entrega/`.

## Economia de tokens (siga sempre)
- Nunca leia `base.css` nem o motor do `timeline.js`, porque eles são fixos. Edite só o bloco TIMELINE.
- Não leia `_originais/`, `_entrega/` nem imagens que você mesmo não precise ver.
- No Figma, use `get_metadata` (barato) para obter posições. Use `get_screenshot` só nos frames do master. Use `get_design_context` só quando faltar algum dado.
- Use Edit pontual em vez de reescrever arquivos. Não mostre código no chat; mostre só o resumo do check.
- Ajustes depois da aprovação: altere só o `layout.css` do formato afetado e rode `check` apenas nele.
