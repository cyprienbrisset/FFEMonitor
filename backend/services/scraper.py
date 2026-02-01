"""
Service de scraping des informations de concours FFE.
Récupère les données publiques sans authentification.
"""

import re
import httpx
from typing import Optional
from dataclasses import dataclass

from backend.utils.logger import get_logger

logger = get_logger("scraper")


@dataclass
class ConcoursInfo:
    """Informations scrappées d'un concours."""

    nom: str | None = None
    lieu: str | None = None
    date_debut: str | None = None
    date_fin: str | None = None
    organisateur: str | None = None
    discipline: str | None = None
    is_open: bool = False  # "Ouvert aux engagements" détecté


class FFEScraper:
    """
    Scraper pour récupérer les informations publiques d'un concours FFE.
    Ne nécessite pas d'authentification.
    """

    BASE_URL = "https://ffecompet.ffe.com/concours"
    TIMEOUT = 15.0

    # Headers pour simuler un navigateur
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    # Patterns regex pour extraire les informations
    PATTERNS = {
        # Nom du concours - patterns spécifiques FFE
        "nom": [
            # Pattern principal: nom suivi de "Organisé par"
            r'([A-ZÀ-Ÿ][^<\n]{10,80}?)\s*Organis[ée]\s+par',
            # Patterns de fallback
            r'>([^<]*(?:Championnat|Grand Prix|Derby|Challenge)[^<]{5,50})<',
            r'Intitul[ée][^:]*:\s*([^<\n]+)',
        ],
        # Lieu - extraire de la balise title ou patterns d'adresse
        "lieu_from_title": [
            r'<title>[^-]+-\s*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\-\']+?)(?:\s*-|\s*<|\s*$)',
            r'Fiche Concours[^-]+-\s*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\-\']+)',
        ],
        # Adresse complète
        "adresse": [
            r'(\d{5}\s+[A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\-\']+)',
            r'<span[^>]*class="[^"]*adresse[^"]*"[^>]*>([^<]+)</span>',
        ],
        # Dates - format DD/MM/YYYY (les 2 premières sont généralement début/fin)
        "dates": [
            r'(\d{2}/\d{2}/\d{4})',
        ],
        # Organisateur
        "organisateur": [
            r'Organisateur[^:]*:\s*([^<\n]+)',
            r'>([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\-\']+)\s*\(\d+\)',
        ],
        # Discipline
        "discipline": [
            r'Discipline[^:]*:\s*([^<\n]+)',
            r'>(?:CSO|CCE|Dressage|Hunter|Western|Endurance|Attelage|Voltige)[^<]*<',
        ],
        # Ouverture aux engagements
        "ouvert": [
            r'[Oo]uvert(?:e)?(?:s)?\s+aux\s+engagements',
            r'[Ee]ngagements?\s+ouverts?',
            r'[Ii]nscriptions?\s+ouvertes?',
        ],
    }

    async def fetch_concours_info(self, numero: int) -> ConcoursInfo:
        """
        Récupère les informations publiques d'un concours.

        Args:
            numero: Numéro du concours FFE

        Returns:
            ConcoursInfo avec les données disponibles
        """
        url = f"{self.BASE_URL}/{numero}"
        info = ConcoursInfo()

        try:
            async with httpx.AsyncClient(
                timeout=self.TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = await client.get(url, headers=self.HEADERS)
                response.raise_for_status()
                html = response.text

                # Extraire le nom
                info.nom = self._extract_nom(html)

                # Extraire le lieu
                info.lieu = self._extract_lieu(html)

                # Extraire les dates
                info.date_debut, info.date_fin = self._extract_dates(html)

                # Extraire l'organisateur
                info.organisateur = self._extract_pattern(html, "organisateur")

                # Extraire la discipline
                info.discipline = self._extract_discipline(html)

                # Si pas de nom, utiliser lieu + discipline comme fallback
                if not info.nom and (info.lieu or info.discipline):
                    parts = []
                    if info.discipline:
                        parts.append(info.discipline)
                    if info.lieu:
                        parts.append(info.lieu)
                    if parts:
                        info.nom = " - ".join(parts)

                # Vérifier si ouvert aux engagements
                info.is_open = self._check_is_open(html)

                logger.debug(
                    f"Concours {numero} scrappé: nom={info.nom}, "
                    f"lieu={info.lieu}, dates={info.date_debut}-{info.date_fin}, "
                    f"ouvert={info.is_open}"
                )

        except httpx.HTTPStatusError as e:
            logger.warning(f"Erreur HTTP pour concours {numero}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Erreur réseau pour concours {numero}: {e}")
        except Exception as e:
            logger.error(f"Erreur scraping concours {numero}: {e}")

        return info

    def _extract_nom(self, html: str) -> Optional[str]:
        """Extrait le nom du concours."""
        # Patterns à exclure
        exclusions = ['ffe compet', 'ffecompet', 'fiche concours']

        for pattern in self.PATTERNS["nom"]:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                nom = match.strip() if isinstance(match, str) else match[0].strip()
                # Nettoyer le nom
                nom = re.sub(r'\s+', ' ', nom)
                nom = nom.replace('&amp;', '&')
                nom = nom.replace('&#39;', "'")
                # Éviter les noms trop courts ou génériques
                if len(nom) > 10:
                    nom_lower = nom.lower()
                    if not any(excl in nom_lower for excl in exclusions):
                        return nom
        return None

    def _extract_lieu(self, html: str) -> Optional[str]:
        """Extrait le lieu du concours depuis le titre de la page."""
        # D'abord essayer d'extraire du titre
        for pattern in self.PATTERNS["lieu_from_title"]:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                lieu = match.group(1).strip()
                lieu = re.sub(r'\s+', ' ', lieu)
                if len(lieu) > 3:
                    return lieu

        # Sinon chercher une adresse
        for pattern in self.PATTERNS["adresse"]:
            match = re.search(pattern, html)
            if match:
                lieu = match.group(1).strip()
                lieu = re.sub(r'\s+', ' ', lieu)
                if len(lieu) > 5:
                    return lieu
        return None

    def _extract_dates(self, html: str) -> tuple[Optional[str], Optional[str]]:
        """Extrait les dates de début et fin (les 2 premières dates trouvées)."""
        # Trouver toutes les dates dans la page
        all_dates = re.findall(self.PATTERNS["dates"][0], html)

        if len(all_dates) >= 2:
            # Les 2 premières sont généralement début et fin du concours
            date_debut = self._normalize_date(all_dates[0])
            date_fin = self._normalize_date(all_dates[1])
            return date_debut, date_fin
        elif len(all_dates) == 1:
            date = self._normalize_date(all_dates[0])
            return date, date

        return None, None

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Convertit une date en format ISO."""
        if not date_str:
            return None

        # Format ISO déjà
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # Format DD/MM/YYYY
        match = re.match(r'^(\d{1,2})/(\d{2})/(\d{4})$', date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day.zfill(2)}"

        return None

    def _extract_pattern(self, html: str, pattern_key: str) -> Optional[str]:
        """Extrait une valeur selon les patterns définis."""
        patterns = self.PATTERNS.get(pattern_key, [])
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'\s+', ' ', value)
                if len(value) > 2:
                    return value
        return None

    def _extract_discipline(self, html: str) -> Optional[str]:
        """Extrait la discipline du concours."""
        # Mapping des codes vers noms complets
        disciplines = {
            'AT': 'Attelage',
            'CSO': 'CSO',
            'CCE': 'CCE',
            'DR': 'Dressage',
            'HU': 'Hunter',
            'EN': 'Endurance',
            'WE': 'Western',
            'VO': 'Voltige',
            'EQ': 'Équitation',
            'PO': 'Pony Games',
        }

        # Chercher le code discipline dans la page (format: "AT Amateur" ou similaire)
        for code, name in disciplines.items():
            pattern = rf'\b{code}\s+(?:Amateur|Club|Pro|Poney)'
            if re.search(pattern, html, re.IGNORECASE):
                return name

        # Chercher les noms complets
        for name in ['Attelage', 'Dressage', 'Hunter', 'Endurance', 'Western', 'Voltige']:
            if name.lower() in html.lower():
                return name

        return None

    def _check_is_open(self, html: str) -> bool:
        """Vérifie si les engagements sont ouverts."""
        for pattern in self.PATTERNS["ouvert"]:
            if re.search(pattern, html, re.IGNORECASE):
                return True
        return False


# Instance globale
scraper = FFEScraper()
