import assert from 'node:assert/strict';
import test from 'node:test';

import { resolveEstimateBlocksForRendering } from './workspaceEstimateCards.js';

function buildSingletonEstimate(title) {
  return {
    title,
    items: [{ name: title, portion: '1 \u4efd', energy: '100 kcal' }],
    total: '100 kcal',
  };
}

test('resolveEstimateBlocksForRendering keeps dish-level multi-card estimates when user mentions each dish', () => {
  const spicyPork = '\u8fa3\u6912\u7092\u8089';
  const whiteRice = '\u767d\u7c73\u996d';
  const estimates = [
    buildSingletonEstimate(spicyPork),
    buildSingletonEstimate(whiteRice),
  ];

  const rendered = resolveEstimateBlocksForRendering({
    estimates,
    mealDescription: `\u4eca\u5929\u4e2d\u5348\u5403\u4e86${spicyPork}\u548c\u4e00\u7897${whiteRice}`,
  });

  assert.equal(rendered?.length, 2);
  assert.equal(rendered?.[0].title, spicyPork);
  assert.equal(rendered?.[1].title, whiteRice);
});

test('resolveEstimateBlocksForRendering groups ingredient-split estimates into per-dish cards for multi-dish query', () => {
  const estimates = [
    buildSingletonEstimate('\u7626\u725b\u8089\u997c'),
    buildSingletonEstimate('\u6c49\u5821\u9762\u5305\uff08\u767d\u9762\u5305\uff09'),
    buildSingletonEstimate('\u6c99\u62c9\u9171/\u5343\u5c9b\u9171\uff08\u4f30\u7b97\uff09'),
    buildSingletonEstimate('\u751f\u83dc/\u756a\u8304\u7b49\u852c\u83dc\uff08\u4f30\u7b97\uff09'),
    buildSingletonEstimate('\u67da\u5b50\u82cf\u6253\u6c34\uff08\u65e0\u7cd6\uff09'),
  ];

  const rendered = resolveEstimateBlocksForRendering({
    estimates,
    mealDescription: '\u4eca\u5929\u4e2d\u5348\u5403\u4e86\u725b\u8089\u6c49\u5821\u548c\u4e00\u676f\u67da\u5b50\u82cf\u6253\u6c34',
  });

  assert.equal(rendered?.length, 2);
  assert.equal(rendered?.[0].title, '\u725b\u8089\u6c49\u5821');
  assert.equal(rendered?.[1].title, '\u67da\u5b50\u82cf\u6253\u6c34');
  assert.equal(rendered?.[0].items.length, 4);
  assert.equal(rendered?.[1].items.length, 1);
});

test('resolveEstimateBlocksForRendering keeps estimates when meal description is unavailable', () => {
  const estimates = [
    buildSingletonEstimate('\u7626\u725b\u8089\u997c'),
    buildSingletonEstimate('\u6c49\u5821\u9762\u5305\uff08\u767d\u9762\u5305\uff09'),
  ];

  const rendered = resolveEstimateBlocksForRendering({
    estimates,
    mealDescription: '',
  });

  assert.equal(rendered?.length, 2);
});

test('resolveEstimateBlocksForRendering falls back to single-card path when only one block exists', () => {
  const estimates = [
    {
      title: '\u8fa3\u6912\u7092\u8089',
      items: [
        { name: '\u732a\u7626\u8089', portion: '80 g', energy: '160 kcal' },
        { name: '\u9752\u6912', portion: '90 g', energy: '35 kcal' },
      ],
      total: '195 kcal',
    },
  ];

  const rendered = resolveEstimateBlocksForRendering({
    estimates,
    mealDescription: '\u8fa3\u6912\u7092\u8089\u70ed\u91cf\u591a\u5c11',
  });

  assert.equal(rendered, null);
});

test('resolveEstimateBlocksForRendering falls back to single-card path for single-dish ingredient-split estimates', () => {
  const estimates = [
    buildSingletonEstimate('\u732a\u7626\u8089'),
    buildSingletonEstimate('\u9752\u6912'),
    buildSingletonEstimate('\u690d\u7269\u6cb9\uff08\u7092\u5236\u7528\uff09'),
  ];

  const rendered = resolveEstimateBlocksForRendering({
    estimates,
    mealDescription: '\u8fa3\u6912\u7092\u8089\u70ed\u91cf\u591a\u5c11',
  });

  assert.equal(rendered, null);
});
