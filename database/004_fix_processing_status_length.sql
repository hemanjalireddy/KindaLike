-- Migration: Fix processing_status column length
-- The column was VARCHAR(20) but 'awaiting_questionnaire' is 22 characters

-- Alter the column to accommodate longer status values
ALTER TABLE preference_analyses
ALTER COLUMN processing_status TYPE VARCHAR(50);

-- Also fix processing_version if needed (for future-proofing)
ALTER TABLE preference_analyses
ALTER COLUMN processing_version TYPE VARCHAR(50);

-- Add a comment documenting the valid status values
COMMENT ON COLUMN preference_analyses.processing_status IS
'Processing status: pending, collecting_data, analyzing, awaiting_questionnaire, aggregating, completed, failed';
