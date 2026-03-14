import assert from 'node:assert/strict';

import { buildFoodLogNavigationState } from './foodLogNavigation.js';

const nextState = buildFoodLogNavigationState('42');

assert.deepEqual(nextState, {
  activeSessionId: '42',
  currentView: 'WORKSPACE',
});

console.log('foodLogNavigation verification passed');
