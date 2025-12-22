-- ============================================
-- Create Free Tier Snapshot Tables
-- ============================================
-- Creates _free tables as exact copies of the source table structures.
-- Run this once to set up the tables.
-- ============================================

-- ============================================
-- 1. Players Page Free (clone structure from source)
-- ============================================
DROP TABLE IF EXISTS api.players_page_free;
CREATE TABLE api.players_page_free (LIKE api.players_page INCLUDING ALL);

-- ============================================
-- 2. Goalies Page Free (clone structure from source)
-- ============================================
DROP TABLE IF EXISTS api.goalies_page_free;
CREATE TABLE api.goalies_page_free (LIKE api.goalies_page INCLUDING ALL);

-- ============================================
-- 3. Teams Page Free (clone structure from source)
-- ============================================
DROP TABLE IF EXISTS api.teams_page_free;
CREATE TABLE api.teams_page_free (LIKE api.teams_page INCLUDING ALL);

-- ============================================
-- 4. Player Stats Page Free (clone structure from source)
-- ============================================
DROP TABLE IF EXISTS api.players_stats_page_free;
CREATE TABLE api.players_stats_page_free (LIKE api.players_stats_page INCLUDING ALL);

-- ============================================
-- 5. Goalie Stats Page Free (clone structure from source)
-- ============================================
DROP TABLE IF EXISTS api.goalie_stats_page_free;
CREATE TABLE api.goalie_stats_page_free (LIKE api.goalie_stats_page INCLUDING ALL);

-- ============================================
-- 6. Playoff Odds Free (clone structure from source)
-- ============================================
DROP TABLE IF EXISTS api.playoff_odds_free;
CREATE TABLE api.playoff_odds_free (LIKE api.playoff_odds INCLUDING ALL);

SELECT 'Free tier tables created successfully!' AS status;
