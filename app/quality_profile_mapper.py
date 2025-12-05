"""
Quality Profile Mapping for Engine Fallback (SPRINT-03)

Handles automatic profile conversion when engine fallback occurs.
This ensures users get equivalent quality profiles when their requested
engine is unavailable and fallback to another engine occurs.

Example:
    User requests: tts_engine=f5tts, quality_profile=f5tts_ultra_natural
    Fallback occurs: f5tts → xtts
    Profile mapped: f5tts_ultra_natural → xtts_expressive
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


# Mapping: Source profile → Equivalent profile
# Format: 'source_engine_profile': 'target_engine_profile'
QUALITY_PROFILE_FALLBACK_MAP: Dict[str, str] = {
    # F5-TTS → XTTS mapping
    'f5tts_ultra_natural': 'xtts_expressive',
    'f5tts_ultra_quality': 'xtts_ultra_quality',
    'f5tts_balanced': 'xtts_balanced',
    'f5tts_fast': 'xtts_fast',
    
    # XTTS → F5-TTS mapping (reverse, for future use)
    'xtts_expressive': 'f5tts_ultra_natural',
    'xtts_ultra_quality': 'f5tts_ultra_quality',
    'xtts_balanced': 'f5tts_balanced',
    'xtts_fast': 'f5tts_fast',
}


def map_quality_profile_for_fallback(
    profile_id: Optional[str],
    requested_engine: str,
    actual_engine: str
) -> Optional[str]:
    """
    Map quality profile when engine fallback occurs.
    
    This function intelligently maps quality profiles between engines
    to ensure users get the closest equivalent quality settings when
    fallback occurs.
    
    Args:
        profile_id: Original quality profile ID (e.g., 'f5tts_ultra_natural')
        requested_engine: Engine user requested (e.g., 'f5tts')
        actual_engine: Engine actually used after fallback (e.g., 'xtts')
    
    Returns:
        Mapped profile ID, or original profile if no mapping needed/found
    
    Examples:
        >>> map_quality_profile_for_fallback('f5tts_ultra_natural', 'f5tts', 'xtts')
        'xtts_expressive'
        
        >>> map_quality_profile_for_fallback('f5tts_balanced', 'f5tts', 'f5tts')
        'f5tts_balanced'  # No fallback, return original
        
        >>> map_quality_profile_for_fallback(None, 'f5tts', 'xtts')
        None  # No profile specified, use engine default
    """
    # No fallback occurred = no mapping needed
    if requested_engine == actual_engine:
        logger.debug(f"No engine fallback, keeping profile: {profile_id}")
        return profile_id
    
    # No profile specified = use engine default
    if not profile_id:
        logger.debug(f"No profile specified, engine {actual_engine} will use default")
        return None
    
    # Try to find mapping
    mapped_profile = QUALITY_PROFILE_FALLBACK_MAP.get(profile_id)
    
    if mapped_profile:
        logger.info(
            f"📊 Quality profile mapped for fallback: {profile_id} → {mapped_profile}",
            extra={
                "original_profile": profile_id,
                "mapped_profile": mapped_profile,
                "requested_engine": requested_engine,
                "actual_engine": actual_engine
            }
        )
        return mapped_profile
    else:
        logger.warning(
            f"⚠️  No quality profile mapping found for '{profile_id}', using engine default",
            extra={
                "profile": profile_id,
                "requested_engine": requested_engine,
                "actual_engine": actual_engine,
                "mapping_available": False
            }
        )
        # Return None to let engine use its default profile
        # (better than using incompatible profile)
        return None


def get_available_mappings() -> Dict[str, str]:
    """
    Get all available profile mappings.
    
    Useful for documentation or debugging.
    
    Returns:
        Dictionary of all profile mappings
    """
    return QUALITY_PROFILE_FALLBACK_MAP.copy()


def is_profile_compatible(profile_id: str, engine: str) -> bool:
    """
    Check if a quality profile is compatible with an engine.
    
    Args:
        profile_id: Quality profile ID (e.g., 'f5tts_balanced')
        engine: Engine name (e.g., 'f5tts', 'xtts')
    
    Returns:
        True if profile is compatible with engine
    
    Examples:
        >>> is_profile_compatible('f5tts_balanced', 'f5tts')
        True
        
        >>> is_profile_compatible('f5tts_balanced', 'xtts')
        False
    """
    if not profile_id:
        return True  # None/empty is always compatible (uses default)
    
    # Check if profile starts with engine name
    return profile_id.lower().startswith(engine.lower())


def suggest_alternative_profile(profile_id: str, target_engine: str) -> Optional[str]:
    """
    Suggest alternative profile for a different engine.
    
    This is a helper function for API responses or error messages.
    
    Args:
        profile_id: Current profile ID
        target_engine: Target engine name
    
    Returns:
        Suggested profile ID for target engine, or None
    
    Examples:
        >>> suggest_alternative_profile('f5tts_ultra_natural', 'xtts')
        'xtts_expressive'
    """
    return QUALITY_PROFILE_FALLBACK_MAP.get(profile_id)
