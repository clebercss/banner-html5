/* timeline.js — motor + timeline da campanha. IDÊNTICO em todos os formatos.
   Edite só em _shared/ e rode `banner.py sync`. Layout por formato fica em layout.css. */
(function () {
  'use strict';

  /* ===== TIMELINE DA CAMPANHA (editar aqui) =====
     t: início (s) · el: id do elemento · anim: keyframe de base.css · dur: duração (s)
     ease: in | out | inout | back | linear (padrão inout) · rep: repetições (ex.: pulso)
     loop: true = só roda se houver próximo ciclo (saída do frame final antes de reiniciar) */
  var TIMELINE = {
    duracao: 10,   // segundos de um ciclo
    loops: 3,      // ciclos desejados; o motor corta para caber no limite do formato
    passos: [
      { t: 0.0, el: 'bg',     anim: 'fade-in',     dur: 0.5 },
      { t: 0.3, el: 'f1-txt', anim: 'entra-esq',   dur: 0.6, ease: 'out' },
      { t: 3.2, el: 'f1-txt', anim: 'sai-esq',     dur: 0.4, ease: 'in' },
      { t: 3.6, el: 'f2-txt', anim: 'entra-baixo', dur: 0.6, ease: 'out' },
      { t: 6.6, el: 'f2-txt', anim: 'fade-out',    dur: 0.4 },
      { t: 7.0, el: 'logo',   anim: 'pop',         dur: 0.5, ease: 'back' },
      { t: 7.3, el: 'cta',    anim: 'entra-baixo', dur: 0.5, ease: 'out' },
      { t: 8.2, el: 'cta',    anim: 'pulso',       dur: 0.6, rep: 2 },
      { t: 9.6, el: 'logo',   anim: 'fade-out',    dur: 0.4, loop: true },
      { t: 9.6, el: 'cta',    anim: 'fade-out',    dur: 0.4, loop: true }
    ]
  };

  /* ===== MOTOR (não editar) ===== */
  var LIMITES = { '1248x250': 15 }, LIMITE_PADRAO = 30;
  var SAIDA = /^(sai-|fade-out)/;
  var ENTRADA = /^(entra-|fade-in|pop|zoom-|revela-|gira-|ken-burns)/;

  function tamanho() {
    var m = document.querySelector('meta[name="ad.size"]'), c = m ? m.content : '';
    var w = /width=(\d+)/.exec(c), h = /height=(\d+)/.exec(c);
    return w && h ? w[1] + 'x' + h[1] : '';
  }

  // Monta a lista de animações CSS de cada elemento para um ciclo.
  // Saídas usam fill "forwards"; só a primeira entrada usa "both" (esconde o elemento antes de entrar).
  function montar(ultimo) {
    var porEl = {}, entrou = {};
    TIMELINE.passos.forEach(function (p) {
      porEl[p.el] = porEl[p.el] || [];
      if (p.loop && ultimo) return;
      var fill = p.fill || (SAIDA.test(p.anim) ? 'forwards'
        : ENTRADA.test(p.anim) ? (entrou[p.el] ? 'forwards' : 'both') : 'none');
      if (ENTRADA.test(p.anim)) entrou[p.el] = true;
      porEl[p.el].push(p.anim + ' ' + p.dur + 's var(--ease-' + (p.ease || 'inout') + ') ' +
        p.t + 's ' + (p.rep || 1) + ' ' + fill);
    });
    return porEl;
  }

  function rodar() {
    var lim = LIMITES[tamanho()] || LIMITE_PADRAO;
    var ciclos = Math.max(1, Math.min(TIMELINE.loops, Math.floor(lim / TIMELINE.duracao)));
    var n = 0;
    function ciclo() {
      var ultimo = ++n >= ciclos, mapa = montar(ultimo);
      Object.keys(mapa).forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;              // elemento omitido neste formato
        el.style.animation = 'none';
        void el.offsetWidth;          // força reinício
        el.style.animation = mapa[id].join(', ') || 'none';
      });
      if (!ultimo) setTimeout(ciclo, TIMELINE.duracao * 1000);
    }
    ciclo();
    document.getElementById('banner').className += ' pronto';
  }

  window.addEventListener('load', rodar);
})();
