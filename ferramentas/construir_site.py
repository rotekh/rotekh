#!/usr/bin/env python3
"""Constrói o site estático da editora em _site/ a partir de livros/.

Uso: python3 ferramentas/construir_site.py
Requer pandoc. Os PDFs devem ter sido gerados antes em pdf/ (gerar-pdfs.sh).
"""
import html, json, os, re, shutil, subprocess, pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "_site"
REPO = os.environ.get("GITHUB_REPOSITORY", "rotekh/rotekh")
GH = f"https://github.com/{REPO}"
EDITORA = "Rotékh"
SLOGAN = "Movimento que vira memória."
GOOGLE_TAG = "AW-18544181096"  # Google Ads; deixe vazio para desligar


def ler_yaml(p):
    d = {}
    for linha in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^(\w+):\s*(.*)$', linha)
        if m:
            d[m[1]] = m[2].strip().strip('"')
    return d


def titulo_md(p):
    for linha in p.read_text(encoding="utf-8").splitlines():
        if linha.startswith("# "):
            return linha[2:].strip()
    return p.stem


def md_para_html(p):
    return subprocess.run(
        ["pandoc", str(p), "-f", "markdown", "-t", "html5", "--shift-heading-level-by=0"],
        capture_output=True, text=True, check=True).stdout


def historico(p):
    rel = p.relative_to(RAIZ).as_posix()
    try:
        out = subprocess.run(
            ["git", "log", "--follow", "--format=%H%x1f%an%x1f%as%x1f%s", "--", rel],
            cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    itens = []
    for linha in out.strip().splitlines():
        h, autor, data, msg = linha.split("\x1f")
        itens.append({"hash": h, "autor": autor, "data": data, "msg": msg,
                      "ver": f"{GH}/blob/{h}/{rel}"})
    return itens


def tag_google():
    if not GOOGLE_TAG:
        return ""
    return f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_TAG}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GOOGLE_TAG}');
</script>
"""


def pagina(titulo, corpo, prof=0, descricao=""):
    base = "../" * prof
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(descricao)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{base}estilo.css">
{tag_google()}</head>
<body>
<header class="topo"><a class="marca" href="{base}index.html">{EDITORA}</a>
<nav><a href="{base}index.html">Livros</a><a href="{base}quem-somos.html">Quem somos</a><a href="{base}como-contribuir.html">Como contribuir</a><a href="{GH}">Repositório</a></nav></header>
<main>
{corpo}
</main>
<footer class="rodape"><p>{EDITORA}, proto-editora aberta. Textos versionados em <a href="{GH}">GitHub</a>; cada mudança fica registrada com autor e data.</p></footer>
</body>
</html>"""


def botao_apoio(meta, prof):
    url = meta.get("crowdfunding", "")
    if url:
        return f'<a class="botao apoio" href="{html.escape(url)}">Apoiar este livro</a>'
    return '<span class="botao apoio desativado" title="Campanha em preparação">Apoiar este livro · em breve</span>'


def construir():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    shutil.copy(RAIZ / "ferramentas" / "estilo.css", SAIDA / "estilo.css")
    if (RAIZ / "pdf").exists():
        shutil.copytree(RAIZ / "pdf", SAIDA / "pdf")

    cartoes = []
    for pasta in sorted((RAIZ / "livros").iterdir()):
        if not (pasta / "livro.yaml").exists():
            continue
        id_ = pasta.name
        meta = ler_yaml(pasta / "livro.yaml")
        caps = sorted((pasta / "capitulos").glob("*.md"))
        dest = SAIDA / id_
        dest.mkdir()
        linhas = []
        for i, cap in enumerate(caps):
            t = titulo_md(cap)
            nome = cap.stem
            hist = historico(cap)
            rel = cap.relative_to(RAIZ).as_posix()
            ant = caps[i - 1].stem if i > 0 else None
            prox = caps[i + 1].stem if i + 1 < len(caps) else None
            corpo_hist = "".join(
                f'<li><time>{h["data"]}</time> <strong>{html.escape(h["autor"])}</strong> '
                f'{html.escape(h["msg"].splitlines()[0])} · <a href="{h["ver"]}">ver esta versão</a></li>'
                for h in hist) or "<li>Sem registros ainda.</li>"
            sugestao = (f'{GH}/issues/new?template=sugestao.yml'
                        f'&title={html.escape("[" + meta.get("titulo", id_) + "] " + t)}')
            navs = ""
            if ant:
                navs += f'<a href="{ant}.html">← anterior</a>'
            navs += f'<a href="index.html">sumário</a>'
            if prox:
                navs += f'<a href="{prox}.html">próximo →</a>'
            corpo = f"""
<p class="trilha"><a href="index.html">{html.escape(meta.get('titulo', id_))}</a></p>
<div class="acoes">
  <a class="botao" href="../pdf/{id_}/{nome}.pdf">Baixar PDF</a>
  <a class="botao secundario" href="{GH}/edit/main/{rel}">Propor edição</a>
  <a class="botao secundario" href="{sugestao}">Enviar sugestão</a>
  <a class="botao secundario" href="#historico">Histórico ({len(hist)})</a>
</div>
<article class="texto">
{md_para_html(cap)}
</article>
<nav class="paginacao">{navs}</nav>
<section id="historico" class="historico">
<h2>Histórico de edições</h2>
<ol>{corpo_hist}</ol>
<p class="nota">Lista completa com as diferenças linha a linha em <a href="{GH}/commits/main/{rel}">GitHub</a>.</p>
</section>"""
            (dest / f"{nome}.html").write_text(
                pagina(f"{t} · {meta.get('titulo', id_)}", corpo, 1), encoding="utf-8")
            ultima = hist[0]["data"] if hist else ""
            linhas.append(f'<li><a href="{nome}.html">{html.escape(t)}</a>'
                          f'<span class="meta">{ultima} · <a href="../pdf/{id_}/{nome}.pdf">PDF</a></span></li>')

        versoes = f'{GH}/releases'
        corpo_livro = f"""
<section class="capa">
  <p class="selo">Versão {html.escape(meta.get('versao', ''))} · {html.escape(meta.get('ano', ''))}</p>
  <h1>{html.escape(meta.get('titulo', id_))}</h1>
  <p class="subtitulo">{html.escape(meta.get('subtitulo', ''))}</p>
  <p class="autor">{html.escape(meta.get('autor', ''))}</p>
  <p class="descricao">{html.escape(meta.get('descricao', ''))}</p>
  <div class="acoes">
    <a class="botao" href="../pdf/{id_}/{id_}-completo.pdf">Baixar livro completo</a>
    {botao_apoio(meta, 1)}
    <a class="botao secundario" href="{versoes}">Edições anteriores</a>
  </div>
</section>
<section>
<h2>Capítulos</h2>
<p class="nota">Cada capítulo pode receber revisões e edições. O livro completo é sempre montado com a última versão aprovada de cada capítulo.</p>
<ol class="capitulos">{''.join(linhas)}</ol>
</section>"""
        (dest / "index.html").write_text(
            pagina(meta.get("titulo", id_), corpo_livro, 1, meta.get("descricao", "")), encoding="utf-8")
        cartoes.append(f"""<a class="cartao" href="{id_}/index.html">
<span class="selo">v{html.escape(meta.get('versao', ''))}</span>
<h3>{html.escape(meta.get('titulo', id_))}</h3>
<p class="subtitulo">{html.escape(meta.get('subtitulo', ''))}</p>
<p class="autor">{html.escape(meta.get('autor', ''))} · {len(caps)} partes</p></a>""")

    inicio = f"""
<section class="abertura">
<h1>{EDITORA}</h1>
<p class="slogan">{SLOGAN}</p>
<p class="lema">Proto-editora aberta. Livros escritos em público, capítulo por capítulo, com revisões de leitores registradas para sempre.</p>
</section>
<section>
<h2>Livros</h2>
<div class="grade">{''.join(cartoes)}</div>
</section>"""
    (SAIDA / "index.html").write_text(pagina(f"{EDITORA} · {SLOGAN}", inicio, descricao=SLOGAN), encoding="utf-8")

    contrib = RAIZ / "CONTRIBUINDO.md"
    (SAIDA / "como-contribuir.html").write_text(
        pagina(f"Como contribuir · {EDITORA}", f'<article class="texto">{md_para_html(contrib)}</article>'),
        encoding="utf-8")
    quem = RAIZ / "QUEM-SOMOS.md"
    (SAIDA / "quem-somos.html").write_text(
        pagina(f"Quem somos · {EDITORA}", f'<article class="texto">{md_para_html(quem)}</article>', descricao=SLOGAN),
        encoding="utf-8")
    (SAIDA / ".nojekyll").write_text("")
    print("site gerado em", SAIDA)


if __name__ == "__main__":
    construir()
