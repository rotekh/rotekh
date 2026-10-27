#!/usr/bin/env bash
# Gera um PDF por capítulo e o PDF do livro completo para cada pasta em livros/
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p pdf
for livro in livros/*/; do
  id=$(basename "$livro")
  mkdir -p "pdf/$id"
  for cap in "$livro"capitulos/*.md; do
    nome=$(basename "$cap" .md)
    pandoc "$cap" -d ferramentas/pdf.yaml -o "pdf/$id/$nome.pdf"
  done
  pandoc "$livro"capitulos/*.md -d ferramentas/pdf.yaml --toc --toc-depth=1 \
    --metadata title="$(sed -n 's/^titulo: //p' "$livro/livro.yaml")" \
    -o "pdf/$id/$id-completo.pdf"
done
