from scripts.get_sources import *
from scripts.get_top_fiis import *
from dotenv import dotenv_values
from scripts.get_news import NoticiasFII

def main():
    # Loading enviorment variables
    config = dotenv_values(".env")

    # Loanding classes
    get_sources = GetSources()
    top_fiis = GetTopFiis()

    # Getting fiis data
    print('Getting fiis data from fundamentus...')
    df_fundamentus = get_sources.get_fundamentus_data()

    # Choosing fiis to anchor reits
    print('Choosing fiis to anchor reits...')
    df_anchor_reits = top_fiis.get_anchor_reits(df_fundamentus,config)

    # Choosing fiis to undervalued reits
    print('Choosing fiis to undervalued reits...')
    df_undervalued_reits = top_fiis.get_undervalued_reits(df_fundamentus,config)

    # Getting fii codes
    print('Getting fii codes...')
    fii_codes = list(set(df_anchor_reits['papel'].unique().tolist() + df_undervalued_reits['papel'].unique().tolist()))
    print(fii_codes)

    # Getting yahoo finance data for all fii 
    print('Getting yahoo finance data for all fii...')
    for fii in fii_codes:
        df_cotacao = get_sources.get_yahoofinance_data(fii)

    print('Getting news for all fii...')
    # Getting news for all fii
    for fii in fii_codes:
        news = NoticiasFII(fii, max_noticias=5, timeout=15)
        news.buscar()
        news.salvar_json()
        

if __name__ == "__main__":
    main()