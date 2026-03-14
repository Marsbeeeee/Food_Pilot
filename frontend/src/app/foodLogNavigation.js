export function buildFoodLogNavigationState(sessionId) {
  return {
    activeSessionId: sessionId,
    currentView: 'WORKSPACE',
  };
}
