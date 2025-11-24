"""Script to approve recent recommendations for testing."""
import sqlite3
import sys

def approve_recommendations(limit=5):
    """Approve the first N recommendations."""
    conn = sqlite3.connect('data/tbcv.db')
    cursor = conn.cursor()

    # Get recent PROPOSED recommendations
    cursor.execute('''
        SELECT id, validation_id, title, description, priority
        FROM recommendations
        WHERE status = 'PROPOSED'
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    recommendations = cursor.fetchall()

    if not recommendations:
        print("No PROPOSED recommendations found in the last 15 minutes.")
        conn.close()
        return 0

    print(f"Found {len(recommendations)} PROPOSED recommendations. Approving them...")

    approved_count = 0
    for rec_id, val_id, title, description, priority in recommendations:
        # Update status to APPROVED
        cursor.execute('''
            UPDATE recommendations
            SET status = 'APPROVED',
                updated_at = datetime('now')
            WHERE id = ?
        ''', (rec_id,))

        print(f"[OK] Approved recommendation {rec_id[:8]}... (priority: {priority})")
        print(f"  Validation: {val_id}")
        print(f"  Title: {title}")
        print(f"  Description: {description[:100] if description else 'N/A'}...")
        print()
        approved_count += 1

    conn.commit()
    conn.close()

    print(f"\n[OK] Successfully approved {approved_count} recommendations")
    return approved_count

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    approve_recommendations(limit)
