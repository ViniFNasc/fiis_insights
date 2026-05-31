import feedparser
import requests
import json
import sys
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable


# ── Model ─────────────────────────────────────────────────────────────────────

@dataclass
class Noticia:
    titulo: str
    fonte: str
    data: str = "—"
    resumo: str = ""
    link: str = ""

    def __str__(self) -> str:
        linhas = [f"  {self.titulo}"]
        linhas.append(f"  🗓  {self.data}  |  📌 {self.fonte}")
        if self.resumo:
            trecho = self.resumo[:160]
            linhas.append(f"  {trecho}{'…' if len(self.resumo) > 160 else ''}")
        if self.link:
            linhas.append(f"  🔗 {self.link}")
        return "\n".join(linhas)


# ── Coletores (Strategy) ──────────────────────────────────────────────────────

class ColetorBase:
    """Interface base para coletores de notícias."""

    nome: str = "Desconhecido"

    def __init__(self, max_noticias: int = 10, timeout: int = 10) -> None:
        self.max_noticias = max_noticias
        self.timeout = timeout
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

    def coletar(self, ticker: str) -> list[Noticia]:
        raise NotImplementedError

    def _formatar_data(self, data_str: str) -> str:
        formatos = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(data_str, fmt).strftime("%d/%m/%Y %H:%M")
            except ValueError:
                continue
        return data_str or "—"

    def _get(self, url: str) -> requests.Response:
        return requests.get(url, headers=self._headers, timeout=self.timeout)


class ColetorGoogleNews(ColetorBase):
    nome = "Google News"

    def coletar(self, ticker: str) -> list[Noticia]:
        query = f"{ticker} FII fundo imobiliário"
        url = (
            "https://news.google.com/rss/search"
            f"?q={query.replace(' ', '+')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        )
        noticias: list[Noticia] = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[: self.max_noticias]:
                resumo = BeautifulSoup(
                    entry.get("summary", ""), "html.parser"
                ).get_text()[:200]
                noticias.append(
                    Noticia(
                        titulo=entry.get("title", "Sem título"),
                        fonte=entry.get("source", {}).get("title", self.nome),
                        data=self._formatar_data(entry.get("published", "")),
                        resumo=resumo,
                        link=entry.get("link", ""),
                    )
                )
        except Exception as e:
            print(f"  [Aviso] {self.nome}: {e}")
        return noticias


class ColetorStatusInvest(ColetorBase):
    nome = "Status Invest"

    def coletar(self, ticker: str) -> list[Noticia]:
        url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker.lower()}"
        noticias: list[Noticia] = []
        try:
            resp = self._get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("div.news-card, article.news-item, div[class*='news']")
            for card in cards[: self.max_noticias]:
                titulo_el = card.select_one("h3, h4, a")
                link_el   = card.select_one("a[href]")
                data_el   = card.select_one("time, span[class*='date'], small")

                titulo = titulo_el.get_text(strip=True) if titulo_el else None
                if not titulo:
                    continue

                link = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = "https://statusinvest.com.br" + link

                noticias.append(
                    Noticia(
                        titulo=titulo,
                        fonte=self.nome,
                        data=data_el.get_text(strip=True) if data_el else "—",
                        link=link,
                    )
                )
        except Exception as e:
            print(f"  [Aviso] {self.nome}: {e}")
        return noticias


class ColetorFundsExplorer(ColetorBase):
    nome = "Funds Explorer"

    def coletar(self, ticker: str) -> list[Noticia]:
        url = f"https://www.fundsexplorer.com.br/funds/{ticker.upper()}"
        noticias: list[Noticia] = []
        try:
            resp = self._get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            items = soup.select("div.news-list__item, li.news-item, article")
            for item in items[: self.max_noticias]:
                titulo_el = item.select_one("h2, h3, h4, a")
                link_el   = item.select_one("a[href]")
                data_el   = item.select_one("time, span[class*='date']")
                resumo_el = item.select_one("p, span[class*='description']")

                titulo = titulo_el.get_text(strip=True) if titulo_el else None
                if not titulo:
                    continue

                link = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = "https://www.fundsexplorer.com.br" + link

                noticias.append(
                    Noticia(
                        titulo=titulo,
                        fonte=self.nome,
                        data=data_el.get_text(strip=True) if data_el else "—",
                        resumo=resumo_el.get_text(strip=True)[:200] if resumo_el else "",
                        link=link,
                    )
                )
        except Exception as e:
            print(f"  [Aviso] {self.nome}: {e}")
        return noticias


# ── Classe Principal ──────────────────────────────────────────────────────────

class NoticiasFII:
    """
    Agrega e gerencia notícias de múltiplas fontes para um determinado FII.

    Exemplo de uso:
        buscador = NoticiasFII("MXRF11")
        buscador.buscar()
        buscador.exibir()
        buscador.salvar_json()

    Ou em uma linha:
        NoticiasFII("HGLG11").buscar().exibir().salvar_json()
    """

    _COLETORES_PADRAO: list[type[ColetorBase]] = [
        ColetorGoogleNews,
        ColetorStatusInvest,
        ColetorFundsExplorer,
    ]

    def __init__(
        self,
        ticker: str,
        *,
        max_noticias: int = 10,
        timeout: int = 10,
        pausa_entre_fontes: float = 0.5,
        coletores: list[type[ColetorBase]] | None = None,
    ) -> None:
        """
        Args:
            ticker:               Código do FII (ex.: 'MXRF11').
            max_noticias:         Máximo de itens por fonte.
            timeout:              Timeout HTTP em segundos.
            pausa_entre_fontes:   Intervalo (s) entre requisições.
            coletores:            Lista de classes coletoras customizadas.
                                  Se None, usa os três coletores padrão.
        """
        self.ticker = ticker.strip().upper()
        self.max_noticias = max_noticias
        self.timeout = timeout
        self.pausa = pausa_entre_fontes
        self._noticias: list[Noticia] = []
        self.caminho_json: str = 'database/news/'

        classes = coletores or self._COLETORES_PADRAO
        self._coletores: list[ColetorBase] = [
            cls(max_noticias=max_noticias, timeout=timeout) for cls in classes
        ]

    # ── Propriedades ──────────────────────────────────────────────────────────

    @property
    def noticias(self) -> list[Noticia]:
        """Retorna as notícias coletadas (lista imutável)."""
        return list(self._noticias)

    @property
    def total(self) -> int:
        return len(self._noticias)

    # ── Métodos Públicos ──────────────────────────────────────────────────────

    def buscar(self) -> "NoticiasFII":
        """Coleta notícias de todas as fontes configuradas. Retorna self (fluent)."""
        
        todas: list[Noticia] = []

        for coletor in self._coletores:
            
            todas.extend(coletor.coletar(self.ticker))
            time.sleep(self.pausa)

        self._noticias = self._processar(todas)
        return self

    def exibir(self) -> "NoticiasFII":
        """Imprime as notícias no terminal. Retorna self (fluent)."""
        sep = "─" * 70
        print(f"\n{'═' * 70}")
        print(f"  📰  Notícias sobre {self.ticker} — {self.total} resultado(s)")
        print(f"{'═' * 70}")

        if not self._noticias:
            print("  Nenhuma notícia encontrada.")
            return self

        for i, n in enumerate(self._noticias, 1):
            print(f"\n{i:>2}. {n}")
            print(f"    {sep}")

        return self

    def salvar_json(self, caminho: str | None = None) -> "NoticiasFII":
        
        if caminho is None:
            ts = datetime.now().strftime(r"%Y-%m-%d")
            caminho = self.caminho_json + f"news_{self.ticker}_{ts}.json"

        payload = {
            "ticker": self.ticker,
            "total": self.total,
            "gerado_em": datetime.now().isoformat(),
            "noticias": [asdict(n) for n in self._noticias],
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        
        return self

    def filtrar_por_fonte(self, fonte: str) -> list[Noticia]:
        """Retorna apenas notícias de uma fonte específica."""
        return [n for n in self._noticias if fonte.lower() in n.fonte.lower()]

    def adicionar_coletor(self, coletor: ColetorBase) -> "NoticiasFII":
        """Adiciona um coletor customizado à lista de fontes."""
        self._coletores.append(coletor)
        return self

    # ── Métodos Privados ──────────────────────────────────────────────────────

    def _processar(self, noticias: list[Noticia]) -> list[Noticia]:
        """Remove duplicatas e ordena por data (mais recente primeiro)."""
        unicas = self._deduplicar(noticias)
        return sorted(unicas, key=lambda n: n.data, reverse=True)

    @staticmethod
    def _deduplicar(noticias: list[Noticia]) -> list[Noticia]:
        vistos: set[str] = set()
        unicas: list[Noticia] = []
        for n in noticias:
            chave = n.titulo.lower().strip()
            if chave not in vistos:
                vistos.add(chave)
                unicas.append(n)
        return unicas

    # ── Dunders ───────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return self.total

    def __iter__(self):
        return iter(self._noticias)

    def __repr__(self) -> str:
        return f"NoticiasFII(ticker={self.ticker!r}, total={self.total})"


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        ticker = input("Digite o ticker do FII (ex.: MXRF11): ").strip()
        salvar = input("Salvar resultados em JSON? (s/N): ").strip().lower() == "s"
    else:
        ticker = args[0]
        salvar = "--salvar" in args or "-s" in args

    if not ticker:
        print("Erro: informe o ticker do FII.")
        sys.exit(1)

    buscador = NoticiasFII(ticker).buscar().exibir()
    if salvar:
        buscador.salvar_json()