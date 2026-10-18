import json

from gerador.agenda import dados_agendamento
from gerador.dados import carregar_site


def test_dados_agendamento(site_beleza, temas_dir):
    d = dados_agendamento(carregar_site(site_beleza, temas_dir))
    assert d["loja"] == "Studio Teste" and d["intervalo"] == 30 and d["pedePet"] is False
    assert d["servicos"][0]["centavos"] == 4500 and d["servicos"][0]["minutos"] == 40
    assert d["servicos"][2]["aPartirDe"] is True
    assert d["adicionais"][0]["centavos"] is None and d["adicionais"][0]["pedeBairro"] is True
    assert [p["id"] for p in d["equipe"]] == ["p1", "p2", "p3"]
    assert d["equipe"][2]["servicos"] == ["corte", "barba", "luzes"]
    assert d["equipe"][1]["funcionamento"] == {"sab": [[540, 720]]}
    assert d["equipe"][0]["funcionamento"] is None
    json.dumps(d)
