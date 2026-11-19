#!/usr/bin/env python3
"""Gera os SVGs do perfil com estilo de Super Mario World (céu azul, blocos '?', tijolos, cano).

Saidas (em assets/):
  atividade-smw.svg  painel com numeros reais do GitHub (repositorios, seguidores, estrelas) e linguagens
  banner-smw.svg     banner fixo do topo do README

Uso:  GITHUB_TOKEN=... python scripts/gerar_svgs.py   (sem token, usa a API publica com limite menor)
Sem dependencias: so a biblioteca padrao.
"""
import html
import json
import os
import urllib.request

USUARIO = "EzequielOrlanes"
SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Paleta de Super Mario World (inspirada, sem sprites)
CEU = "#5c94fc"
NUVEM = "#ffffff"
BLOCO = "#f8b800"
BLOCO_BORDA = "#000000"
TIJOLO = "#c84c0c"
TIJOLO_CLARO = "#e45c10"
CANO = "#00a800"
CANO_ESCURO = "#005800"

CORES_LINGUAGEM = {
    "Python": "#3572a5", "C++": "#f34b7d", "C": "#8a8a8a", "JavaScript": "#f1e05a",
    "Kotlin": "#a97bff", "Jupyter Notebook": "#da5b0b", "HTML": "#e34c26", "CSS": "#563d7c",
}


def api(caminho, token):
    cabecalhos = {"Accept": "application/vnd.github+json", "User-Agent": "perfil-smw"}
    if token:
        cabecalhos["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com" + caminho, headers=cabecalhos)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def coletar(token):
    usuario = api(f"/users/{USUARIO}", token)
    repos, pagina = [], 1
    while True:
        lote = api(f"/users/{USUARIO}/repos?per_page=100&type=owner&page={pagina}", token)
        if not lote:
            break
        repos += lote
        pagina += 1
    proprios = [r for r in repos if not r.get("fork")]
    estrelas = sum(r.get("stargazers_count", 0) for r in proprios)
    linguagens = {}
    for r in proprios:
        for lingua, bytes_ in api(f"/repos/{r['full_name']}/languages", token).items():
            linguagens[lingua] = linguagens.get(lingua, 0) + bytes_
    return {
        "repositorios": len(proprios),
        "seguidores": usuario.get("followers", 0),
        "estrelas": estrelas,
        "linguagens": sorted(linguagens.items(), key=lambda x: -x[1])[:6],
    }


def nuvem(x, y, s=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})" fill="{NUVEM}">'
            '<ellipse cx="0" cy="0" rx="34" ry="18"/><ellipse cx="-22" cy="6" rx="22" ry="14"/>'
            '<ellipse cx="24" cy="6" rx="24" ry="15"/></g>')


def chao(largura, y, altura=36):
    partes = [f'<rect x="0" y="{y}" width="{largura}" height="{altura}" fill="{TIJOLO}"/>']
    for linha in range(0, altura, 12):
        yy = y + linha
        partes.append(f'<line x1="0" y1="{yy}" x2="{largura}" y2="{yy}" stroke="{TIJOLO_CLARO}" stroke-width="2"/>')
        deslocamento = 0 if (linha // 12) % 2 == 0 else 30
        for xx in range(deslocamento, largura, 60):
            partes.append(f'<line x1="{xx}" y1="{yy}" x2="{xx}" y2="{yy + 12}" stroke="{TIJOLO_CLARO}" stroke-width="2"/>')
    return "".join(partes)


def cano(x, y_base, altura=70):
    return (f'<rect x="{x}" y="{y_base - altura}" width="58" height="{altura}" fill="{CANO}" stroke="{CANO_ESCURO}" stroke-width="3"/>'
            f'<rect x="{x - 6}" y="{y_base - altura}" width="70" height="16" fill="{CANO}" stroke="{CANO_ESCURO}" stroke-width="3"/>')


def texto(x, y, conteudo, tamanho=18, cor="#ffffff", anchor="start", peso="bold"):
    # texto escuro (sobre o bloco amarelo) fica sem contorno; texto claro ganha contorno preto
    contorno = "" if cor == "#000000" else ' stroke="#000000" stroke-width="3" paint-order="stroke" stroke-linejoin="round"'
    return (f'<text x="{x}" y="{y}" font-family="Courier New, Consolas, monospace" font-size="{tamanho}" '
            f'font-weight="{peso}" fill="{cor}" text-anchor="{anchor}"{contorno}>{html.escape(conteudo)}</text>')


def bloco_interrogacao(x, y, w, h, valor, rotulo):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{BLOCO}" stroke="{BLOCO_BORDA}" stroke-width="4"/>'
            f'<rect x="{x + 6}" y="{y + 6}" width="{w - 12}" height="{h - 12}" rx="3" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.6"/>'
            + texto(x + 16, y + 28, "?", 22, "#000000", peso="bold")
            + texto(x + w / 2, y + h / 2 + 12, str(valor), 34, "#000000", "middle")
            + texto(x + w / 2, y + h - 14, rotulo, 14, "#000000", "middle"))


def svg_atividade(dados):
    largura, altura = 860, 330
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Atividade no GitHub">',
              f'<rect width="{largura}" height="{altura}" fill="{CEU}"/>',
              nuvem(120, 60, 1.0), nuvem(640, 40, 0.8), nuvem(760, 130, 0.6),
              texto(40, 52, "ATIVIDADE", 26)]
    cartoes = [("repositorios", "REPOS"), ("seguidores", "SEGUIDORES"), ("estrelas", "ESTRELAS")]
    x = 40
    for chave, rotulo in cartoes:
        partes.append(bloco_interrogacao(x, 80, 240, 120, dados[chave], rotulo))
        x += 265
    # barra de linguagens
    total = sum(v for _, v in dados["linguagens"]) or 1
    x = 40
    barra_y, barra_h, barra_w = 230, 22, 780
    partes.append(f'<rect x="{x - 4}" y="{barra_y - 4}" width="{barra_w + 8}" height="{barra_h + 8}" rx="6" fill="#000000"/>')
    for lingua, bytes_ in dados["linguagens"]:
        w = barra_w * bytes_ / total
        cor = CORES_LINGUAGEM.get(lingua, "#9e9e9e")
        partes.append(f'<rect x="{x:.1f}" y="{barra_y}" width="{w:.1f}" height="{barra_h}" fill="{cor}"/>')
        x += w
    legenda = "   ".join(f"{lingua} {100 * v / total:.0f}%" for lingua, v in dados["linguagens"][:5])
    partes.append(texto(40, 280, legenda, 14))
    partes.append(chao(largura, altura - 36))
    partes.append("</svg>")
    return "".join(partes)


def svg_banner():
    largura, altura = 860, 220
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Ezequiel Orlanes, desenvolvedor backend">',
              f'<rect width="{largura}" height="{altura}" fill="{CEU}"/>',
              nuvem(90, 50, 0.9), nuvem(700, 40, 1.0), nuvem(420, 140, 0.6),
              texto(40, 96, "EZEQUIEL ORLANES", 44),
              texto(40, 130, "DESENVOLVEDOR BACKEND", 20, "#ffffff"),
              texto(40, 156, "Sistemas de Informação · UFMG", 16, "#ffffff", peso="normal"),
              f'<rect x="600" y="92" width="48" height="48" rx="6" fill="{BLOCO}" stroke="{BLOCO_BORDA}" stroke-width="4"/>',
              texto(616, 126, "?", 26, "#000000"),
              cano(740, altura - 36, 90),
              chao(largura, altura - 36)]
    partes.append("</svg>")
    return "".join(partes)


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    os.makedirs(SAIDA, exist_ok=True)
    dados = coletar(token)
    with open(os.path.join(SAIDA, "atividade-smw.svg"), "w", encoding="utf-8") as f:
        f.write(svg_atividade(dados))
    with open(os.path.join(SAIDA, "banner-smw.svg"), "w", encoding="utf-8") as f:
        f.write(svg_banner())
    print(json.dumps({k: v for k, v in dados.items() if k != "linguagens"}, ensure_ascii=False),
          "linguagens:", len(dados["linguagens"]))


if __name__ == "__main__":
    main()
