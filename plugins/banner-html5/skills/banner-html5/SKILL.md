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
- **Cada formato é independente**: a pasta `<WxH>/` tem os próprios `index.html`, `base.css`, `timeline.js`, `layout.css` e `assets/`. Nunca crie pasta compartilhada nem referencie arquivos fora da pasta do formato (o `check` acusa). Detalhes em `references/timeline.md`.
- Preview: o `index.html` na raiz da campanha (modelo em `templates/preview.html`) mostra **só os formatos já prontos**. Regere com `$B preview` sempre que um formato ficar pronto.

## 0. Preparação (obrigatório, antes de qualquer arquivo)
Rode `$B setup` uma vez no início da sessão. Ele instala sozinho o que faltar (Pillow e svgo) e responde em uma linha. Se algo falhar, repasse a linha ao usuário e siga: o `otimizar` funciona com menos compressão.

**Pasta de destino:**
Toda campanha precisa ser salva numa pasta local escolhida pelo usuário. Nunca salve numa pasta temporária ou de sessão.
- Se a ferramenta `request_directory` existir, chame-a **sem path** (ela abre o seletor de pastas) e depois `change_directory` com a pasta devolvida. Até o fim do turno, use o caminho absoluto.
- Se ela não existir, pergunte o caminho da pasta na mesma mensagem em que pedir o link.
- Se a sessão já estiver numa pasta escolhida pelo usuário para esta campanha, use essa pasta e não pergunte de novo.
- A campanha fica em `<pasta>/<nome-curto>/` (por exemplo `cabore`). No Windows, prefira caminhos curtos (limite de 260 caracteres).

## 1. Briefing (no máximo 2 rodadas)
1. Se o link ou o card não veio no argumento, peça **só isso**, em uma linha, lembrando o usuário de enviar o link com `node-id` (ver `references/figma.md`).
2. **Formatos**: uma chamada AskUserQuestion com 4 perguntas multiSelect que, juntas, listam os 14 formatos **um a um** (nunca agrupados). Cada opção tem como label o formato e como descrição o peso e a duração. Avise na pergunta 1 que as quatro perguntas formam uma lista só, e que as que não tiverem formato desejado podem ficar em branco ou receber "Other: nenhum".
   - Formatos (1/4): `1248x250` (200KB · 15s), `970x250`, `970x150`, `970x90` (150KB · 30s)
   - Formatos (2/4): `320x480`, `480x320` (150KB · 30s), `320x50` (50KB · 30s), `300x250` (60KB · 30s)
   - Formatos (3/4): `728x90`, `468x60`, `160x600`, `120x600` (60KB · 30s)
   - Formatos (4/4): `120x60`, `90x60` (60KB · 30s)
   **Campo aberto:** todas as perguntas têm o campo "Other". Escreva no texto da pergunta 1: *"Prefere digitar? Use 'Other' em qualquer pergunta e escreva os formatos separados por vírgula (ex.: 300x250, 728x90, 320x50)."*
   Junte os formatos marcados com os digitados, normalize (`300 x 250`, `300X250` e `300×250` viram `300x250`) e tire os repetidos. Se algum formato digitado não estiver na tabela, avise e pergunte o peso e a duração dele antes de seguir; depois passe-o ao `novo` como `WxH:KB:segundos` (ex.: `300x600:150:30`). O script já normaliza texto livre e guarda os formatos novos em `formatos_extra.txt`.
   Essa chamada não depende do Figma: faça-a logo depois do passo 0, antes de ler a campanha.
3. Leia a campanha da forma mais barata (`references/figma.md`) e faça **uma única** chamada AskUserQuestion com 3 perguntas:
   - **Mood**: 3 opções deduzidas da campanha (presets em `references/timeline.md`).
   - **Animações por frame**: 2 ou 3 propostas concretas baseadas na campanha (ex.: "F1 texto entra-esq out 0.5s · F2 produto pop back · CTA pulso"), com a primeira marcada como (Recomendado).
   - **Observações**: "Nenhuma" / "Tenho observações" (o usuário escreve em Other).

## 2. Master
1. Escolha como master o formato com mais elementos e frames detalhados (de preferência o 300x250, se estiver na lista).
2. `$B novo <campanha> <master>` cria só a pasta do master a partir do template.
3. Coloque os assets do master em `<master>/assets/`, usando os mesmos nomes de arquivo que valerão para todos os formatos.
4. Edite `<master>/index.html`: um `<img class="el">` por linha, com ids que descrevem o elemento (`f1-titulo`, `produto`, `cta`).
5. Edite `<master>/timeline.js` (só o bloco TIMELINE) e `<master>/layout.css`.
6. Rode `$B otimizar <campanha> <master>`, depois `$B check <campanha> <master>`. O `otimizar` só comprime se o formato passar do peso máximo: dentro do limite, os assets ficam originais. Acima, ele comprime do maior asset ao menor e para assim que cabe. Não comprima imagens por conta própria.
7. Rode `$B preview <campanha>` (o index mostra só o master) e peça a aprovação antes de adaptar os outros formatos.

## 3. Adaptação dos outros formatos → subagente `banner-adaptador`
Antes de delegar, rode `$B clonar <campanha> <master> <formatos alvo>`: cada formato recebe a **própria cópia** de `index.html` (com o tamanho certo), `base.css` e `timeline.js` do master. A partir daí cada formato é independente; se um formato precisar de timeline ou elementos diferentes, edite os arquivos dele mesmo.

Delegue **uma única** chamada Agent (`subagent_type: banner-html5:banner-adaptador`) para todos os formatos restantes. Se forem mais de 7 formatos, divida em 2 chamadas paralelas. O subagente já roda em Sonnet com esforço baixo. O prompt deve ser curto e conter só:
- o comando `B` completo, com o caminho absoluto do banner.py;
- caminho da campanha e formato master;
- lista de formatos alvo, cada um com sua fonte de layout (fileKey + node-id do frame, ou caminho do print);
- de onde vêm os assets (pasta exportada pelo usuário ou "baixar via Figma");
- elementos que não existem em algum formato (ele marca `omitir:`).

Não repasse o briefing inteiro: o subagente não mexe na timeline. Confira apenas o resumo que ele devolver.

## 4. Entrega
`$B check <campanha>` → `$B zip <campanha>` → `$B preview <campanha>`. O `zip` também gera o backup do último frame de cada formato (`_entrega/<campanha>_<formato>_backup.jpg`, via Chrome/Edge headless). Informe ao usuário a tabela do check, os zips e backups em `_entrega/` e o `index.html` de preview.
Se o usuário informar seções de mídia (ex.: GCOM, UAC, AFILIADOS), grave `secoes.txt` na campanha (`GCOM: 970x250, 970x150, 300x250`, uma seção por linha) antes do preview.

## Economia de tokens (siga sempre)
- Nunca leia `base.css` nem o motor do `timeline.js`, porque eles são fixos. Edite só o bloco TIMELINE.
- Mudou a timeline do master depois de clonar? Rode `$B clonar` de novo para os formatos que devem seguir o master (layout.css e assets/ nunca são sobrescritos).
- Não leia `_originais/`, `_entrega/` nem imagens que você mesmo não precise ver.
- No Figma, use `get_metadata` (barato) para obter posições. Use `get_screenshot` só nos frames do master. Use `get_design_context` só quando faltar algum dado.
- Use Edit pontual em vez de reescrever arquivos. Não mostre código no chat; mostre só o resumo do check.
- Ajustes depois da aprovação: altere só o `layout.css` do formato afetado e rode `check` apenas nele.
