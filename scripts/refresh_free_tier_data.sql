-- ============================================
-- Free Tier Data Refresh Script
-- ============================================
-- Copies data from premium tables to free tier snapshot tables.
-- Run every Tuesday at 11:30 PM ET after dbt models complete.
--
-- This script is atomic - if any table fails, the entire transaction rolls back,
-- preserving the previous week's data for free users.
-- ============================================

BEGIN;

-- ============================================
-- 1. Player Cards
-- ============================================
TRUNCATE api.players_page_free;
INSERT INTO api.players_page_free
SELECT * FROM api.players_page;

-- ============================================
-- 2. Goalie Cards
-- ============================================
TRUNCATE api.goalies_page_free;
INSERT INTO api.goalies_page_free
SELECT * FROM api.goalies_page;

-- ============================================
-- 3. Team Cards
-- ============================================
TRUNCATE api.teams_page_free;
INSERT INTO api.teams_page_free
SELECT * FROM api.teams_page;

-- ============================================
-- 4. Player Stats
-- ============================================
TRUNCATE api.players_stats_page_free;
INSERT INTO api.players_stats_page_free
SELECT * FROM api.players_stats_page;

-- ============================================
-- 5. Goalie Stats
-- ============================================
TRUNCATE api.goalie_stats_page_free;
INSERT INTO api.goalie_stats_page_free
SELECT * FROM api.goalie_stats_page;

-- ============================================
-- 6. Playoff Odds
-- ============================================
TRUNCATE api.playoff_odds_free;
INSERT INTO api.playoff_odds_free
SELECT * FROM api.playoff_odds;

COMMIT;

-- Log completion
SELECT 'Free tier data refresh completed at ' || NOW() AS status;
