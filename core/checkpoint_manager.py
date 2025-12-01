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
