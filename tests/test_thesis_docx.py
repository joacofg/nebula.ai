from scripts.thesis import docx


def test_completar_notes_are_dropped():
    text = "Antes.\n\n> COMPLETAR (Joaquín): revisalo y\n> reescribilo.\n\nDespués.\n"
    assert docx.drop_notes(text) == "Antes.\n\nDespués.\n"


def test_index_goes_between_acknowledgements_and_organisation():
    text = (
        "# Preliminares\n\n## 1. Carátula\n\n**Universidad**\nTítulo largo\n\n"
        "## 2. Agradecimientos\n\nGracias.\n\n## 4. Organización del documento\n\nTexto.\n"
    )
    out = docx.preliminaries(text)
    assert out.index("# 2. Agradecimientos") < out.index("# 3. Índice") < out.index("# 4. Organización")
    assert "TOC \\o" in out
    assert "# Preliminares" not in out
    assert "Carátula" not in out


def test_cover_joins_a_bold_title_wrapped_over_two_lines():
    xml = docx.cover(docx._join_wrapped("**Enrutamiento inteligente para\ngateways self-hosted**\nAlumno: X\n"))
    assert "<w:b/>" in xml
    assert "Enrutamiento inteligente para gateways self-hosted" in xml
    assert "Alumno: X" in xml


def test_every_chapter_of_the_repo_is_in_the_source():
    text = docx.source()
    for title in ("# 6. Resumen", "# 12. Conclusiones", "# 15. Glosario", "# 3. Índice"):
        assert title in text
    assert "COMPLETAR" not in text
