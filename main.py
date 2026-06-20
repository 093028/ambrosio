"""
AMBROSIO — Conferência automática de pagamentos
Compara 0-LOTES PGTOS x 0-ITAU e gera relatorio_divergencias.xlsx
"""

from pathlib import Path
from src.reader import localizar_pdfs, extrair_lote_pgtos, extrair_itau
from src.comparator import comparar_pagamentos
from src.reporter import gerar_relatorio


def main():
    print("=" * 60)
    print("  AMBROSIO — Conferência de Pagamentos")
    print("=" * 60)

    # 1. Solicitar pasta
    pasta_str = input("\nInforme o caminho da pasta com os PDFs:\n> ").strip().strip('"')
    pasta = Path(pasta_str)

    if not pasta.exists():
        print(f"\n❌ Pasta não encontrada: {pasta}")
        return

    # 2. Localizar PDFs
    print("\n🔍 Localizando arquivos PDF...")
    caminho_lote, caminho_itau = localizar_pdfs(pasta)

    if not caminho_lote:
        print("❌ Arquivo de LOTES PGTOS não encontrado na pasta.")
        return
    if not caminho_itau:
        print("❌ Arquivo do ITAÚ não encontrado na pasta.")
        return

    print(f"   ✔ Lote:  {caminho_lote.name}")
    print(f"   ✔ Itaú:  {caminho_itau.name}")

    # 3. Extrair dados
    print("\n📄 Extraindo dados dos PDFs...")
    df_lote = extrair_lote_pgtos(caminho_lote)
    df_itau = extrair_itau(caminho_itau)

    print(f"   ✔ {len(df_lote)} registros no Lote")
    print(f"   ✔ {len(df_itau)} registros no Itaú")

    if df_lote.empty and df_itau.empty:
        print("\n⚠️  Nenhum dado extraído. Verifique o layout dos PDFs.")
        return

    # 4. Comparar
    print("\n⚖️  Comparando pagamentos...")
    df_resultado = comparar_pagamentos(df_lote, df_itau)

    divergentes = len(df_resultado[df_resultado["status"] != "OK"])
    print(f"   ✔ {divergentes} divergência(s) encontrada(s)")

    # 5. Gerar relatório
    pasta_saida = Path(__file__).parent / "outputs"
    data_ref = pasta.name  # Usa o nome da pasta como referência de data
    print(f"\n📊 Gerando relatório...")
    caminho_relatorio = gerar_relatorio(df_resultado, pasta_saida, data_ref)

    print(f"\n✅ Relatório gerado com sucesso!")
    print(f"   📁 {caminho_relatorio}")
    print("=" * 60)


if __name__ == "__main__":
    main()
