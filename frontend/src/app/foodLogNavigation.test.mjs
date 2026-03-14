import assert from 'node:assert/strict';
import test from 'node:test';

import { buildFoodLogNavigationState } from './foodLogNavigation.js';

test('buildFoodLogNavigationState routes back to the workspace chat', () => {
  const nextState = buildFoodLogNavigationState('42');

  assert.deepEqual(nextState, {
    activeSessionId: '42',
    currentView: 'WORKSPACE',
  });
});
