# banner-html5

Criador de animados HTML5 para campanhas: plugin do Claude Code que gera banners animados a partir de frames do Figma ou de prints, respeitando os limites de peso e de duração de cada formato.

O plugin instala:
- a skill `/banner-html5`, com template, timeline compartilhada, scripts e references;
- o subagente `banner-adaptador`, que roda em Sonnet com esforço baixo e adapta o master para os outros formatos.

## 1. Dependências
Precisa ter **Python 3.8+**, **Node.js** e **Chrome ou Edge** instalados (o navegador gera o backup JPG do último frame no `zip`). O Pillow e o svgo a skill instala sozinha no primeiro uso (`banner.py setup`). O pngquant é opcional e reduz mais o peso dos PNG (baixe em pngquant.org e coloque no PATH).

## 2. Instalar o plugin
```bash
claude plugin marketplace add clebercss/banner-html5
```
```bash
claude plugin install banner-html5@banners-html5
```
Para testar localmente, sem GitHub, use o caminho desta pasta no lugar de `clebercss/banner-html5`.

## 3. Figma (opcional)
Instale e autorize o conector do Figma (`/mcp`). Sem ele, a skill trabalha com prints.

## Uso
```
/banner-html5 https://www.figma.com/design/<fileKey>/...?node-id=12-345
```

## Atualizar
Edite os arquivos, aumente o número de `version` em `plugins/banner-html5/.claude-plugin/plugin.json` e em `.claude-plugin/marketplace.json`, e faça o push. Quem já instalou atualiza com:
```bash
claude plugin marketplace update banners-html5
```
