"""Dados de agendamento entregues à página (JSON)."""
from gerador.formatos import centavos


def _cent(valor):
    return None if valor is None else centavos(valor)


def dados_agendamento(site: dict) -> dict:
    ag = site["agenda"]
    ids = [s["id"] for s in site["servicos"]]
    return {
        "loja": site["site"]["nome"], "intervalo": ag["intervalo"], "dias": ag["dias"],
        "pedePet": ag["pede_pet"], "funcionamento": ag["funcionamento"],
        "servicos": [{"id": s["id"], "nome": s["nome"], "categoria": s["categoria"],
                      "minutos": s["duracao"], "centavos": _cent(s["preco"]),
                      "aPartirDe": s["a_partir_de"],
                      "porte": {k: centavos(x) for k, x in s["porte"].items()} if s["porte"] else None}
                     for s in site["servicos"]],
        "adicionais": [{"id": a["id"], "nome": a["nome"], "centavos": _cent(a["preco"]),
                        "pedeBairro": a["pede_bairro"]} for a in site["adicionais"]],
        "equipe": [{"id": f"p{i}", "nome": p["nome"], "especialidade": p["especialidade"],
                    "servicos": p["servicos"] or list(ids), "funcionamento": p["funcionamento"]}
                   for i, p in enumerate(site["equipe"], 1)],
    }
