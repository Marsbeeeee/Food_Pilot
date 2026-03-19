import assert from 'node:assert/strict';
import test from 'node:test';

import { buildWorkspaceMessagePresentation } from './workspaceMessagePresentation.js';

test('buildWorkspaceMessagePresentation returns estimate card shape with extended fields', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_estimate',
    title: 'Chicken Avocado Salad',
    confidence: 'high',
    description: 'Protein-forward meal.',
    items: [
      { name: 'Chicken', portion: '150g', energy: '240 kcal' },
      { name: 'Avocado', portion: '1/2', energy: '180 kcal' },
    ],
    total: '420 kcal',
  });

  assert.equal(presentation.variant, 'meal_estimate');
  assert.equal(presentation.title, 'Chicken Avocado Salad');
  assert.equal(presentation.confidence, 'high');
  assert.equal(presentation.total, '420 kcal');
  assert.equal(presentation.items.length, 2);
  assert.equal(presentation.estimates, null);
  assert.equal(presentation.suggestion, null);
  assert.ok(presentation.ingredientColumnLabel);
  assert.ok(presentation.portionColumnLabel);
  assert.ok(presentation.energyColumnLabel);
  assert.ok(presentation.proteinColumnLabel);
  assert.ok(presentation.carbsColumnLabel);
  assert.ok(presentation.fatColumnLabel);
  assert.ok(presentation.totalLabel);
});

test('buildWorkspaceMessagePresentation returns recommendation card and fallback title', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_recommendation',
    content: 'Choose grilled chicken salad with pumpkin soup.',
    description: 'Lower fat while keeping satiety.',
  });

  assert.equal(presentation.variant, 'meal_recommendation');
  assert.equal(presentation.content, 'Choose grilled chicken salad with pumpkin soup.');
  assert.equal(presentation.description, 'Lower fat while keeping satiety.');
  assert.ok(presentation.title);
  assert.ok(presentation.eyebrow);
  assert.ok(presentation.badgeLabel);
  assert.ok(presentation.reasonLabel);
  assert.ok(presentation.contentLabel);
});

test('buildWorkspaceMessagePresentation keeps text messages as plain bubbles', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'text',
    content: 'Grilling usually uses less oil than deep frying.',
  });

  assert.deepEqual(presentation, {
    variant: 'text',
    content: 'Grilling usually uses less oil than deep frying.',
  });
});
