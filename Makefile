# Build targets for the data-driven CV.
#
# Usage:
#   make academic        # render + compile the academic variant to build/academic/academic.pdf
#   make lint            # lint the bibliography
#   make test            # run the Python test suite
#   make clean           # remove all generated artifacts
#
# Requires: python3 with deps from pyproject.toml (use `make venv` to bootstrap),
# xelatex, biber, latexmk.

PY       := .venv/bin/python
PYTEST   := .venv/bin/pytest
VARIANTS := academic

BUILD_DIR      = build/$(1)
TEX_FRAGMENTS  = $(BUILD_DIR)/tex
PDF_OUT        = $(BUILD_DIR)/$(1).pdf

.PHONY: all venv lint test clean $(VARIANTS)

all: $(VARIANTS)

venv:
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip
	.venv/bin/pip install --quiet -e ".[dev]"

# Per-variant build: render fragments, then compile the PDF with latexmk.
# The variant is selected at compile time via -usepretex that redefines
# \cvvariant. cv-llt.tex's \providecommand{\cvvariant}{academic} provides a
# sane default when no override is passed (e.g., direct Overleaf compiles).
define variant_rule
$(1): lint
	$$(PY) -m tools.render $(1)
	mkdir -p build/$(1)
	latexmk -xelatex -output-directory=build/$(1) \
		-jobname=$(1) \
		-interaction=nonstopmode \
		-halt-on-error \
		-usepretex='\def\cvvariant{$(1)}' \
		cv-llt.tex
endef

$(foreach v,$(VARIANTS),$(eval $(call variant_rule,$(v))))

lint:
	$(PY) -m tools.lint_bib own-bib.bib

test:
	$(PYTEST)

clean:
	rm -rf build
