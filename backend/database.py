"""
Gestion de la base de données SQLite pour EngageWatch.
Opérations CRUD asynchrones sur la table concours.
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.models import StatutConcours
from backend.utils.logger import get_logger

logger = get_logger("database")

# Schéma de la table concours
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS concours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER UNIQUE NOT NULL,
    statut TEXT DEFAULT 'ferme',
    notifie INTEGER DEFAULT 0,
    last_check TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """Gestionnaire de base de données SQLite asynchrone."""

    def __init__(self, db_path: str | Path | None = None):
        """
        Initialise le gestionnaire de base de données.

        Args:
            db_path: Chemin vers le fichier SQLite
        """
        self.db_path = Path(db_path) if db_path else settings.database_full_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Établit la connexion et initialise la base."""
        # Créer le dossier data si nécessaire
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Créer la table si elle n'existe pas
        await self._connection.execute(CREATE_TABLE_SQL)
        await self._connection.commit()

        logger.info(f"Base de données connectée: {self.db_path}")

    async def disconnect(self) -> None:
        """Ferme la connexion à la base de données."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Base de données déconnectée")

    @property
    def connection(self) -> aiosqlite.Connection:
        """Retourne la connexion active."""
        if not self._connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def add_concours(self, numero: int) -> dict | None:
        """
        Ajoute un concours à surveiller.

        Args:
            numero: Numéro du concours FFE

        Returns:
            Le concours créé ou None si déjà existant
        """
        try:
            cursor = await self.connection.execute(
                """
                INSERT INTO concours (numero, statut, notifie, created_at)
                VALUES (?, 'ferme', 0, ?)
                """,
                (numero, datetime.now().isoformat()),
            )
            await self.connection.commit()

            # Récupérer le concours créé
            return await self.get_concours_by_numero(numero)

        except aiosqlite.IntegrityError:
            logger.warning(f"Concours {numero} déjà surveillé")
            return None

    async def get_concours_by_numero(self, numero: int) -> dict | None:
        """
        Récupère un concours par son numéro.

        Args:
            numero: Numéro du concours

        Returns:
            Le concours ou None si non trouvé
        """
        cursor = await self.connection.execute(
            "SELECT * FROM concours WHERE numero = ?",
            (numero,),
        )
        row = await cursor.fetchone()

        if row:
            return self._row_to_dict(row)
        return None

    async def get_all_concours(self) -> list[dict]:
        """
        Récupère tous les concours surveillés.

        Returns:
            Liste des concours
        """
        cursor = await self.connection.execute(
            "SELECT * FROM concours ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    async def get_concours_non_notifies(self) -> list[dict]:
        """
        Récupère les concours non encore notifiés.

        Returns:
            Liste des concours à surveiller activement
        """
        cursor = await self.connection.execute(
            "SELECT * FROM concours WHERE notifie = 0"
        )
        rows = await cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    async def update_statut(
        self,
        numero: int,
        statut: StatutConcours,
        notifie: bool = False,
    ) -> bool:
        """
        Met à jour le statut d'un concours.

        Args:
            numero: Numéro du concours
            statut: Nouveau statut
            notifie: Marquer comme notifié

        Returns:
            True si mis à jour, False sinon
        """
        cursor = await self.connection.execute(
            """
            UPDATE concours
            SET statut = ?, notifie = ?, last_check = ?
            WHERE numero = ?
            """,
            (statut.value, int(notifie), datetime.now().isoformat(), numero),
        )
        await self.connection.commit()

        updated = cursor.rowcount > 0
        if updated:
            logger.info(f"Concours {numero} mis à jour: {statut.value}, notifié={notifie}")
        return updated

    async def update_last_check(self, numero: int) -> bool:
        """
        Met à jour le timestamp de dernière vérification.

        Args:
            numero: Numéro du concours

        Returns:
            True si mis à jour, False sinon
        """
        cursor = await self.connection.execute(
            "UPDATE concours SET last_check = ? WHERE numero = ?",
            (datetime.now().isoformat(), numero),
        )
        await self.connection.commit()
        return cursor.rowcount > 0

    async def delete_concours(self, numero: int) -> bool:
        """
        Supprime un concours de la surveillance.

        Args:
            numero: Numéro du concours

        Returns:
            True si supprimé, False sinon
        """
        cursor = await self.connection.execute(
            "DELETE FROM concours WHERE numero = ?",
            (numero,),
        )
        await self.connection.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Concours {numero} retiré de la surveillance")
        return deleted

    async def count_concours(self) -> int:
        """Retourne le nombre total de concours surveillés."""
        cursor = await self.connection.execute("SELECT COUNT(*) FROM concours")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def count_concours_ouverts(self) -> int:
        """Retourne le nombre de concours ouverts."""
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM concours WHERE statut != 'ferme'"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    # =========================================================================
    # Helpers
    # =========================================================================

    def _row_to_dict(self, row: aiosqlite.Row) -> dict:
        """Convertit une row SQLite en dictionnaire."""
        return {
            "id": row["id"],
            "numero": row["numero"],
            "statut": row["statut"],
            "notifie": bool(row["notifie"]),
            "last_check": (
                datetime.fromisoformat(row["last_check"])
                if row["last_check"]
                else None
            ),
            "created_at": datetime.fromisoformat(row["created_at"]),
        }


# Instance globale
db = Database()
