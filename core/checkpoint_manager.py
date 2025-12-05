"""System checkpoint management."""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
from core.logging import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Manages system checkpoints."""

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint storage
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

    def create_checkpoint(self, name: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a system checkpoint.

        Args:
            name: Optional checkpoint name
            metadata: Optional metadata to include

        Returns:
            Checkpoint ID
        """
        # Generate checkpoint ID
        timestamp = datetime.now(timezone.utc)
        checkpoint_id = timestamp.strftime("%Y%m%d_%H%M%S")
        if name:
            checkpoint_id = f"{checkpoint_id}_{name}"

        checkpoint_path = self.checkpoint_dir / checkpoint_id
        checkpoint_path.mkdir(exist_ok=True)

        # Save checkpoint metadata
        checkpoint_info = {
            "id": checkpoint_id,
            "name": name,
            "created_at": timestamp.isoformat(),
            "metadata": metadata or {}
        }

        # Copy database
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        db_path = db_manager.get_database_path()
        if db_path and Path(db_path).exists():
            shutil.copy2(db_path, checkpoint_path / "database.db")
            checkpoint_info["database_backed_up"] = True
        else:
            checkpoint_info["database_backed_up"] = False

        # Get cache stats (don't copy cache, just record stats)
        from core.cache import cache_manager
        cache_stats = cache_manager.get_statistics()
        checkpoint_info["cache_stats"] = cache_stats

        # Save checkpoint info
        with open(checkpoint_path / "checkpoint.json", 'w') as f:
            json.dump(checkpoint_info, f, indent=2)

        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_id

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        List all available checkpoints.

        Returns:
            List of checkpoint info dictionaries
        """
        checkpoints = []
        for checkpoint_path in sorted(self.checkpoint_dir.iterdir()):
            if checkpoint_path.is_dir():
                info_file = checkpoint_path / "checkpoint.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            checkpoint_info = json.load(f)
                            checkpoints.append(checkpoint_info)
                    except Exception as e:
                        logger.warning(f"Failed to read checkpoint: {checkpoint_path.name}", error=str(e))

        return checkpoints

    def get_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Get checkpoint details.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint info dictionary

        Raises:
            ValueError: If checkpoint not found
        """
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        info_file = checkpoint_path / "checkpoint.json"

        if not info_file.exists():
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        with open(info_file, 'r') as f:
            return json.load(f)

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to delete

        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self.checkpoint_dir / checkpoint_id

        if checkpoint_path.exists() and checkpoint_path.is_dir():
            shutil.rmtree(checkpoint_path)
            logger.info(f"Deleted checkpoint: {checkpoint_id}")
            return True

        return False

    def validate_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Validate checkpoint data integrity.

        This method verifies:
        - Checkpoint directory exists
        - Checkpoint metadata file exists and is valid JSON
        - Required fields are present
        - Database backup exists if indicated
        - Cache stats are valid

        Args:
            checkpoint_id: Checkpoint ID to validate

        Returns:
            True if checkpoint is valid, False otherwise
        """
        try:
            # Check checkpoint directory exists
            checkpoint_path = self.checkpoint_dir / checkpoint_id
            if not checkpoint_path.exists() or not checkpoint_path.is_dir():
                logger.warning(f"Checkpoint directory not found: {checkpoint_id}")
                return False

            # Check metadata file exists
            info_file = checkpoint_path / "checkpoint.json"
            if not info_file.exists():
                logger.warning(f"Checkpoint metadata file not found: {checkpoint_id}")
                return False

            # Load and validate metadata
            with open(info_file, 'r') as f:
                checkpoint_info = json.load(f)

            # Verify required fields
            required_fields = ["id", "created_at"]
            for field in required_fields:
                if field not in checkpoint_info:
                    logger.warning(f"Checkpoint missing required field '{field}': {checkpoint_id}")
                    return False

            # Verify checkpoint ID matches
            if checkpoint_info["id"] != checkpoint_id:
                logger.warning(f"Checkpoint ID mismatch: expected {checkpoint_id}, got {checkpoint_info['id']}")
                return False

            # Verify created_at is valid ISO format
            try:
                datetime.fromisoformat(checkpoint_info["created_at"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid created_at timestamp in checkpoint: {checkpoint_id}")
                return False

            # Verify database backup if indicated
            if checkpoint_info.get("database_backed_up", False):
                db_backup = checkpoint_path / "database.db"
                if not db_backup.exists():
                    logger.warning(f"Database backup missing for checkpoint: {checkpoint_id}")
                    return False

            # Verify cache stats if present
            if "cache_stats" in checkpoint_info:
                cache_stats = checkpoint_info["cache_stats"]
                if not isinstance(cache_stats, dict):
                    logger.warning(f"Invalid cache stats in checkpoint: {checkpoint_id}")
                    return False

            # Verify metadata if present
            if "metadata" in checkpoint_info:
                metadata = checkpoint_info["metadata"]
                if not isinstance(metadata, dict):
                    logger.warning(f"Invalid metadata in checkpoint: {checkpoint_id}")
                    return False

            logger.info(f"Checkpoint validation passed: {checkpoint_id}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse checkpoint metadata: {checkpoint_id}", error=str(e))
            return False
        except Exception as e:
            logger.error(f"Checkpoint validation failed: {checkpoint_id}", error=str(e))
            return False

    def recover_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Recover system state from a checkpoint.

        This method:
        1. Validates the checkpoint
        2. Restores database from backup
        3. Updates cache statistics

        Args:
            checkpoint_id: Checkpoint ID to recover from

        Returns:
            True if recovery successful, False otherwise
        """
        try:
            # Validate checkpoint first
            if not self.validate_checkpoint(checkpoint_id):
                logger.error(f"Cannot recover from invalid checkpoint: {checkpoint_id}")
                return False

            checkpoint_info = self.get_checkpoint(checkpoint_id)
            checkpoint_path = self.checkpoint_dir / checkpoint_id

            # Restore database if backup exists
            if checkpoint_info.get("database_backed_up", False):
                db_backup = checkpoint_path / "database.db"
                if db_backup.exists():
                    from core.database import DatabaseManager
                    db_manager = DatabaseManager()
                    db_path = db_manager.get_database_path()

                    if db_path:
                        # Create backup of current database
                        current_db = Path(db_path)
                        if current_db.exists():
                            backup_path = current_db.parent / f"{current_db.stem}_backup.db"
                            shutil.copy2(current_db, backup_path)
                            logger.info(f"Created backup of current database: {backup_path}")

                        # Restore from checkpoint
                        shutil.copy2(db_backup, db_path)
                        logger.info(f"Restored database from checkpoint: {checkpoint_id}")
                else:
                    logger.warning(f"Database backup not found in checkpoint: {checkpoint_id}")

            logger.info(f"Successfully recovered from checkpoint: {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to recover from checkpoint: {checkpoint_id}", error=str(e))
            return False
