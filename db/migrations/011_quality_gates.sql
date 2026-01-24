-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 011_quality_gates.sql
-- Description: Quality gate views and helpers for validation workflows
-- ─────────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────────
-- View: Claims without evidence
-- Lists all claims that have no associated evidence_span records
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW evidence.v_claims_without_evidence AS
SELECT
    c.id AS claim_id,
    c.claim_type,
    c.claim_text,
    c.confidence,
    c.revision_id,
    r.document_id,
    d.doc_id,
    d.title AS document_title,
    c.created_at
FROM evidence.claim c
JOIN evidence.document_revision r ON c.revision_id = r.id
JOIN evidence.document d ON r.document_id = d.id
LEFT JOIN evidence.evidence_span es ON c.id = es.claim_id
WHERE es.id IS NULL
ORDER BY d.doc_id, c.created_at;

COMMENT ON VIEW evidence.v_claims_without_evidence IS
    'Quality gate: Claims that lack any supporting evidence spans';

-- ─────────────────────────────────────────────────────────────────────────────
-- View: Document validation summary
-- Shows validation status per document
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW evidence.v_document_validation_summary AS
SELECT
    d.id AS document_id,
    d.doc_id,
    d.title,
    d.status,
    COUNT(DISTINCT c.id) AS total_claims,
    COUNT(DISTINCT CASE WHEN es.id IS NOT NULL THEN c.id END) AS claims_with_evidence,
    COUNT(DISTINCT CASE WHEN es.id IS NULL THEN c.id END) AS claims_without_evidence,
    CASE
        WHEN COUNT(DISTINCT c.id) = 0 THEN 'no_claims'
        WHEN COUNT(DISTINCT CASE WHEN es.id IS NULL THEN c.id END) = 0 THEN 'ready'
        ELSE 'incomplete'
    END AS validation_status
FROM evidence.document d
LEFT JOIN evidence.document_revision r ON d.id = r.document_id
LEFT JOIN evidence.claim c ON r.id = c.revision_id
LEFT JOIN evidence.evidence_span es ON c.id = es.claim_id
GROUP BY d.id, d.doc_id, d.title, d.status
ORDER BY d.doc_id;

COMMENT ON VIEW evidence.v_document_validation_summary IS
    'Summary of claim evidence coverage per document';

-- ─────────────────────────────────────────────────────────────────────────────
-- Function: Check if document can be validated
-- Returns error message if validation would fail, NULL if OK
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION evidence.check_document_validation(p_document_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_claims_without_evidence INT;
    v_total_claims INT;
    v_doc_id TEXT;
BEGIN
    -- Get document info
    SELECT doc_id INTO v_doc_id
    FROM evidence.document WHERE id = p_document_id;

    IF v_doc_id IS NULL THEN
        RETURN 'Document not found: ' || p_document_id::TEXT;
    END IF;

    -- Count claims and coverage (DISTINCT to handle multiple evidence_spans per claim)
    SELECT
        COUNT(DISTINCT c.id),
        COUNT(DISTINCT c.id) FILTER (WHERE es.id IS NULL)
    INTO v_total_claims, v_claims_without_evidence
    FROM evidence.claim c
    JOIN evidence.document_revision r ON c.revision_id = r.id
    LEFT JOIN evidence.evidence_span es ON c.id = es.claim_id
    WHERE r.document_id = p_document_id;

    IF v_total_claims = 0 THEN
        RETURN 'Document ' || v_doc_id || ' has no claims to validate';
    END IF;

    IF v_claims_without_evidence > 0 THEN
        RETURN 'Document ' || v_doc_id || ' has ' || v_claims_without_evidence ||
               ' claims without evidence (of ' || v_total_claims || ' total)';
    END IF;

    -- All checks passed
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION evidence.check_document_validation(UUID) IS
    'Returns NULL if document is ready for validation, error message otherwise';

-- ─────────────────────────────────────────────────────────────────────────────
-- Function: Validate document (update status if all claims have evidence)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION evidence.validate_document(p_document_id UUID)
RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
DECLARE
    v_error TEXT;
BEGIN
    -- Check validation requirements
    v_error := evidence.check_document_validation(p_document_id);

    IF v_error IS NOT NULL THEN
        RETURN QUERY SELECT FALSE, v_error;
        RETURN;
    END IF;

    -- Update document status
    UPDATE evidence.document
    SET status = 'validated'
    WHERE id = p_document_id
      AND status != 'validated';

    RETURN QUERY SELECT TRUE, 'Document validated successfully'::TEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION evidence.validate_document(UUID) IS
    'Attempts to validate a document; fails if any claims lack evidence';
