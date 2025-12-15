/**
 * Feature Flags Module
 *
 * Provides feature flag management with environment-based configuration.
 */

export {
  // Types
  type Environment,
  type FeatureFlagConfig,
  type FeatureFlagsState,

  // Manager & Functions
  featureFlags,
  detectEnvironment,
  isFeatureEnabled,
  initializeFeatureFlags,
  DEFAULT_FEATURE_FLAGS,

  // React Hooks
  useFeatureFlag,
  useFeatureFlags,
} from './featureFlags'
