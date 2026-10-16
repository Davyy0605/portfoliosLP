// Status "Aberto agora" a partir de [[horarios]]. Incluído inline na landing pelo Jinja
// e testado em tests/js/aberto.test.js. Na dúvida (texto que não entende), devolve null e o bloco fica oculto.
function statusAberto(horarios, agora) {
  var DIAS = { dom: 0, seg: 1, ter: 2, qua: 3, qui: 4, sex: 5, sab: 6 };
  var NOMES = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];
  var norm = function (t) { return String(t || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim(); };
  var dia = function (p) { var d = DIAS[norm(p).replace(/^de\s+/, "").slice(0, 3)]; return d === undefined ? null : d; };
  var diasDe = function (txt) {
    var t = norm(txt).replace(/^de\s+/, "").replace(/[-\s]feira/g, "");
    if (/^(todos os dias|diariamente)$/.test(t)) return [0, 1, 2, 3, 4, 5, 6];
    t = t.replace(/fins? de semana/g, "sab e dom");
    var r = [];
    var partes = t.split(/\s*,\s*|\s+e\s+/);
    for (var i = 0; i < partes.length; i++) {
      var ab = partes[i].split(/\s*[-–]\s*|\s+a\s+|\s+ate\s+/);
      if (ab.length > 2) return null;
      var a = dia(ab[0]), b = ab.length === 2 ? dia(ab[1]) : a;
      if (a === null || b === null) return null;
      for (var d = a; ; d = (d + 1) % 7) { r.push(d); if (d === b) break; }
    }
    return r;
  };
  var faixas = [];
  for (var i = 0; i < horarios.length; i++) {
    var h = horarios[i];
    if (norm(h.horas) === "fechado") continue;
    if (/fechado/.test(norm(h.horas))) return null;
    var hs = Array.from(String(h.horas).matchAll(/(\d{1,2})(?:h|:)(\d{2})?(?:min)?/g));
    var dias = diasDe(h.dias);
    if (!dias || hs.length < 2 || hs.length % 2) return null;
    for (var k = 0; k < hs.length; k += 2) {
      var ini = +hs[k][1] * 60 + (+hs[k][2] || 0);
      var fim = +hs[k + 1][1] * 60 + (+hs[k + 1][2] || 0);
      if (fim <= ini) fim += 1440;
      for (var j = 0; j < dias.length; j++) faixas.push({ d: dias[j], ini: ini, fim: fim, txtIni: hs[k][0], txtFim: hs[k + 1][0] });
    }
  }
  if (!faixas.length) return null;
  var hoje = agora.getDay(), m = agora.getHours() * 60 + agora.getMinutes();
  var aberta = faixas.find(function (f) {
    return (f.d === hoje && m >= f.ini && m < f.fim) || (f.d === (hoje + 6) % 7 && m + 1440 < f.fim);
  });
  if (aberta) return { aberto: true, texto: "Aberto agora, até " + aberta.txtFim };
  for (var n = 0; n < 8; n++) {
    var dd = (hoje + n) % 7;
    var prox = faixas.filter(function (x) { return x.d === dd && (n > 0 || x.ini > m); }).sort(function (a, b) { return a.ini - b.ini; })[0];
    if (prox) return { aberto: false, texto: "Fechado agora. Abre " + (n === 0 ? "hoje" : n === 1 ? "amanhã" : NOMES[dd]) + " às " + prox.txtIni };
  }
  return null;
}
