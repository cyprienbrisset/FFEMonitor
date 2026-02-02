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
    nom TEXT,
    statut TEXT DEFAULT 'ferme',
    notifie INTEGER DEFAULT 0,
    last_check TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    date_debut TEXT,
    date_fin TEXT,
    lieu TEXT
);
"""

# Tables pour les statistiques
CREATE_CHECK_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS check_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concours_numero INTEGER NOT NULL,
    checked_at TEXT NOT NULL,
    statut_before TEXT,
    statut_after TEXT,
    response_time_ms INTEGER,
    success INTEGER DEFAULT 1,
    FOREIGN KEY (concours_numero) REFERENCES concours(numero) ON DELETE CASCADE
);
"""

CREATE_OPENING_EVENTS_SQL = """
CREATE TABLE IF NOT EXISTS opening_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concours_numero INTEGER NOT NULL,
    opened_at TEXT NOT NULL,
    statut TEXT NOT NULL,
    notification_sent_at TEXT,
    FOREIGN KEY (concours_numero) REFERENCES concours(numero) ON DELETE CASCADE
);
"""

# Index pour améliorer les performances des requêtes de stats
CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_check_history_numero ON check_history(concours_numero);
CREATE INDEX IF NOT EXISTS idx_check_history_checked_at ON check_history(checked_at);
CREATE INDEX IF NOT EXISTS idx_opening_events_numero ON opening_events(concours_numero);
CREATE INDEX IF NOT EXISTS idx_opening_events_opened_at ON opening_events(opened_at);
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

        # Activer les foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")

        # Créer les tables si elles n'existent pas
        await self._connection.execute(CREATE_TABLE_SQL)
        await self._connection.execute(CREATE_CHECK_HISTORY_SQL)
        await self._connection.execute(CREATE_OPENING_EVENTS_SQL)
        await self._connection.executescript(CREATE_INDEXES_SQL)
        await self._connection.commit()

        # Migrer la table concours si nécessaire (ajouter nouvelles colonnes)
        await self._migrate_concours_table()

        logger.info(f"Base de données connectée: {self.db_path}")

    async def _migrate_concours_table(self) -> None:
        """Ajoute les nouvelles colonnes à la table concours si elles n'existent pas."""
        try:
            cursor = await self._connection.execute("PRAGMA table_info(concours)")
            columns = [row[1] for row in await cursor.fetchall()]

            if "nom" not in columns:
                await self._connection.execute(
                    "ALTER TABLE concours ADD COLUMN nom TEXT"
                )
                logger.info("Colonne nom ajoutée à la table concours")

            if "date_debut" not in columns:
                await self._connection.execute(
                    "ALTER TABLE concours ADD COLUMN date_debut TEXT"
                )
                logger.info("Colonne date_debut ajoutée à la table concours")

            if "date_fin" not in columns:
                await self._connection.execute(
                    "ALTER TABLE concours ADD COLUMN date_fin TEXT"
                )
                logger.info("Colonne date_fin ajoutée à la table concours")

            if "lieu" not in columns:
                await self._connection.execute(
                    "ALTER TABLE concours ADD COLUMN lieu TEXT"
                )
                logger.info("Colonne lieu ajoutée à la table concours")

            await self._connection.commit()
        except Exception as e:
            logger.warning(f"Migration table concours: {e}")

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

    async def update_concours_info(
        self,
        numero: int,
        nom: str | None = None,
        date_debut: str | None = None,
        date_fin: str | None = None,
        lieu: str | None = None,
    ) -> bool:
        """
        Met à jour les informations scrappées d'un concours.

        Args:
            numero: Numéro du concours
            nom: Nom du concours
            date_debut: Date de début (format ISO)
            date_fin: Date de fin (format ISO)
            lieu: Lieu du concours

        Returns:
            True si mis à jour, False sinon
        """
        cursor = await self.connection.execute(
            """
            UPDATE concours
            SET nom = COALESCE(?, nom),
                date_debut = COALESCE(?, date_debut),
                date_fin = COALESCE(?, date_fin),
                lieu = COALESCE(?, lieu)
            WHERE numero = ?
            """,
            (nom, date_debut, date_fin, lieu, numero),
        )
        await self.connection.commit()
        return cursor.rowcount > 0

    # Alias for backward compatibility
    async def update_concours_dates(
        self,
        numero: int,
        date_debut: str | None = None,
        date_fin: str | None = None,
        lieu: str | None = None,
    ) -> bool:
        """Alias pour update_concours_info (rétrocompatibilité)."""
        return await self.update_concours_info(
            numero=numero,
            date_debut=date_debut,
            date_fin=date_fin,
            lieu=lieu,
        )

    # =========================================================================
    # Statistics Operations
    # =========================================================================

    async def record_check(
        self,
        concours_numero: int,
        statut_before: str | None,
        statut_after: str | None,
        response_time_ms: int,
        success: bool = True,
    ) -> int:
        """
        Enregistre une vérification dans l'historique.

        Args:
            concours_numero: Numéro du concours vérifié
            statut_before: Statut avant vérification
            statut_after: Statut après vérification
            response_time_ms: Temps de réponse en ms
            success: Vérification réussie ou non

        Returns:
            ID de l'enregistrement créé
        """
        cursor = await self.connection.execute(
            """
            INSERT INTO check_history
            (concours_numero, checked_at, statut_before, statut_after, response_time_ms, success)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                concours_numero,
                datetime.now().isoformat(),
                statut_before,
                statut_after,
                response_time_ms,
                int(success),
            ),
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def record_opening(
        self,
        concours_numero: int,
        statut: str,
        notification_sent_at: str | None = None,
    ) -> int:
        """
        Enregistre un événement d'ouverture de concours.

        Args:
            concours_numero: Numéro du concours
            statut: Type d'ouverture (engagement/demande)
            notification_sent_at: Timestamp de notification (optionnel)

        Returns:
            ID de l'enregistrement créé
        """
        cursor = await self.connection.execute(
            """
            INSERT INTO opening_events
            (concours_numero, opened_at, statut, notification_sent_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                concours_numero,
                datetime.now().isoformat(),
                statut,
                notification_sent_at,
            ),
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def get_concours_stats(self, numero: int) -> dict:
        """
        Récupère les statistiques détaillées d'un concours.

        Args:
            numero: Numéro du concours

        Returns:
            Dictionnaire avec les statistiques
        """
        # Nombre total de vérifications
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM check_history WHERE concours_numero = ?",
            (numero,),
        )
        total_checks = (await cursor.fetchone())[0]

        # Vérifications réussies
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM check_history WHERE concours_numero = ? AND success = 1",
            (numero,),
        )
        successful_checks = (await cursor.fetchone())[0]

        # Temps de réponse moyen
        cursor = await self.connection.execute(
            "SELECT AVG(response_time_ms) FROM check_history WHERE concours_numero = ? AND success = 1",
            (numero,),
        )
        avg_response = (await cursor.fetchone())[0] or 0

        # Événements d'ouverture
        cursor = await self.connection.execute(
            "SELECT * FROM opening_events WHERE concours_numero = ? ORDER BY opened_at DESC",
            (numero,),
        )
        openings = [dict(row) for row in await cursor.fetchall()]

        return {
            "numero": numero,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "success_rate": (successful_checks / total_checks * 100) if total_checks > 0 else 0,
            "avg_response_time_ms": round(avg_response, 2),
            "opening_events": openings,
        }

    async def get_global_stats(self) -> dict:
        """
        Récupère les statistiques globales de l'application.

        Returns:
            Dictionnaire avec les statistiques globales
        """
        # Total des concours
        total_concours = await self.count_concours()
        concours_ouverts = await self.count_concours_ouverts()

        # Total des vérifications
        cursor = await self.connection.execute("SELECT COUNT(*) FROM check_history")
        total_checks = (await cursor.fetchone())[0]

        # Vérifications dans les dernières 24h
        yesterday = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM check_history WHERE checked_at >= ?",
            (yesterday,),
        )
        checks_today = (await cursor.fetchone())[0]

        # Total des ouvertures détectées
        cursor = await self.connection.execute("SELECT COUNT(*) FROM opening_events")
        total_openings = (await cursor.fetchone())[0]

        # Temps de réponse moyen global
        cursor = await self.connection.execute(
            "SELECT AVG(response_time_ms) FROM check_history WHERE success = 1"
        )
        avg_response = (await cursor.fetchone())[0] or 0

        # Taux de succès global
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM check_history WHERE success = 1"
        )
        successful = (await cursor.fetchone())[0]

        return {
            "total_concours": total_concours,
            "concours_ouverts": concours_ouverts,
            "total_checks": total_checks,
            "checks_today": checks_today,
            "total_openings": total_openings,
            "avg_response_time_ms": round(avg_response, 2),
            "success_rate": (successful / total_checks * 100) if total_checks > 0 else 0,
        }

    async def get_activity_data(self, period: str = "24h") -> dict:
        """
        Récupère les données d'activité pour le graphique.

        Args:
            period: "24h" ou "7d"

        Returns:
            Données formatées pour Chart.js
        """
        if period == "7d":
            # Données par jour sur 7 jours
            from_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
            from_date = from_date.replace(day=from_date.day - 6)
            group_format = "%Y-%m-%d"
            label_format = "%d/%m"
            intervals = 7
        else:
            # Données par heure sur 24h
            from_date = datetime.now().replace(minute=0, second=0, microsecond=0)
            from_date = from_date.replace(hour=from_date.hour - 23)
            group_format = "%Y-%m-%d %H"
            label_format = "%H:00"
            intervals = 24

        from_date_str = from_date.isoformat()

        # Récupérer les vérifications
        cursor = await self.connection.execute(
            f"""
            SELECT strftime('{group_format}', checked_at) as period,
                   COUNT(*) as checks,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM check_history
            WHERE checked_at >= ?
            GROUP BY period
            ORDER BY period
            """,
            (from_date_str,),
        )
        check_data = {row[0]: {"checks": row[1], "successful": row[2]} for row in await cursor.fetchall()}

        # Récupérer les ouvertures
        cursor = await self.connection.execute(
            f"""
            SELECT strftime('{group_format}', opened_at) as period,
                   COUNT(*) as openings
            FROM opening_events
            WHERE opened_at >= ?
            GROUP BY period
            ORDER BY period
            """,
            (from_date_str,),
        )
        opening_data = {row[0]: row[1] for row in await cursor.fetchall()}

        # Construire les labels et données
        labels = []
        checks = []
        openings = []

        current = from_date
        for _ in range(intervals):
            if period == "7d":
                key = current.strftime(group_format)
                label = current.strftime(label_format)
                current = current.replace(day=current.day + 1)
            else:
                key = current.strftime(group_format)
                label = current.strftime(label_format)
                current = current.replace(hour=current.hour + 1)

            labels.append(label)
            data = check_data.get(key, {"checks": 0, "successful": 0})
            checks.append(data["checks"])
            openings.append(opening_data.get(key, 0))

        return {
            "labels": labels,
            "checks": checks,
            "openings": openings,
            "period": period,
        }

    async def get_concours_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """
        Récupère les concours dans une plage de dates.

        Args:
            start_date: Date de début (format ISO)
            end_date: Date de fin (format ISO)

        Returns:
            Liste des concours dans la plage
        """
        cursor = await self.connection.execute(
            """
            SELECT * FROM concours
            WHERE date_debut IS NOT NULL
            AND date_debut >= ? AND date_debut <= ?
            ORDER BY date_debut
            """,
            (start_date, end_date),
        )
        rows = await cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    # =========================================================================
    # Helpers
    # =========================================================================

    def _row_to_dict(self, row: aiosqlite.Row) -> dict:
        """Convertit une row SQLite en dictionnaire."""
        result = {
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

        # Ajouter les champs optionnels s'ils existent
        if "nom" in row.keys():
            result["nom"] = row["nom"]
        if "date_debut" in row.keys():
            result["date_debut"] = row["date_debut"]
        if "date_fin" in row.keys():
            result["date_fin"] = row["date_fin"]
        if "lieu" in row.keys():
            result["lieu"] = row["lieu"]

        return result


# Instance globale
db = Database()
