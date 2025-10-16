"""Fix scaffolding order_index to start from 1

Revision ID: 7a8b9c0d1e2f
Revises: 6d4c0c8f0f8a
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '6d4c0c8f0f8a'
branch_labels = None
depends_on = None


def upgrade():
    """Fix scaffolding order_index to start from 1 for each video"""
    # Get database connection
    connection = op.get_bind()
    
    # Get all videos with their scaffoldings
    videos_query = """
        SELECT DISTINCT video_id 
        FROM scaffoldings 
        ORDER BY video_id
    """
    
    videos = connection.execute(sa.text(videos_query)).fetchall()
    
    for video_row in videos:
        video_id = video_row[0]
        
        # Get scaffoldings for this video ordered by current order_index
        scaffoldings_query = """
            SELECT id, order_index 
            FROM scaffoldings 
            WHERE video_id = :video_id 
            ORDER BY order_index, id
        """
        
        scaffoldings = connection.execute(
            sa.text(scaffoldings_query), 
            {"video_id": video_id}
        ).fetchall()
        
        # Update order_index to start from 1
        for index, (scaffolding_id, _) in enumerate(scaffoldings, 1):
            update_query = """
                UPDATE scaffoldings 
                SET order_index = :new_order 
                WHERE id = :scaffolding_id
            """
            
            connection.execute(
                sa.text(update_query), 
                {"new_order": index, "scaffolding_id": scaffolding_id}
            )
    
    print("Scaffolding order_index migration completed successfully")


def downgrade():
    """Revert scaffolding order_index back to 0-based indexing"""
    # Get database connection
    connection = op.get_bind()
    
    # Get all videos with their scaffoldings
    videos_query = """
        SELECT DISTINCT video_id 
        FROM scaffoldings 
        ORDER BY video_id
    """
    
    videos = connection.execute(sa.text(videos_query)).fetchall()
    
    for video_row in videos:
        video_id = video_row[0]
        
        # Get scaffoldings for this video ordered by current order_index
        scaffoldings_query = """
            SELECT id, order_index 
            FROM scaffoldings 
            WHERE video_id = :video_id 
            ORDER BY order_index, id
        """
        
        scaffoldings = connection.execute(
            sa.text(scaffoldings_query), 
            {"video_id": video_id}
        ).fetchall()
        
        # Update order_index to start from 0
        for index, (scaffolding_id, _) in enumerate(scaffoldings):
            update_query = """
                UPDATE scaffoldings 
                SET order_index = :new_order 
                WHERE id = :scaffolding_id
            """
            
            connection.execute(
                sa.text(update_query), 
                {"new_order": index, "scaffolding_id": scaffolding_id}
            )
    
    print("Scaffolding order_index reverted to 0-based indexing")
