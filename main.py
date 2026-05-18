from scripts.get_sources import *
from scripts.get_top_fiis import *
from dotenv import dotenv_values


def main():
    # Loading enviorment variables
    config = dotenv_values(".env")

    # Loanding classes
    get_sources = GetSources()
    top_fiis = GetTopFiis()

    # Getting fiis data
    df_fundamentus = get_sources.get_fundamentus_data()

    # Getting fii codes
    fii_codes = df_fundamentus['papel'].unique()

    # Getting yahoo finance data for all fii 
    for fii in fii_codes:
        df_cotacao = get_sources.get_yahoofinance_data(fii)


    # Choosing fiis to anchor reits
    df_anchor_reits = top_fiis.get_anchor_reits(df_fundamentus,config)


if __name__ == "__main__":
    main()