import test from 'node:test';
import assert from 'node:assert/strict';
import { cleanText, elementDelta, waterfallBottoms, jobNotification } from './src/presentationData.ts';

test('normalizes actual and escaped newlines and tabs without dropping content', () => {
 assert.equal(cleanText(' 甲\r\n乙\t丙\r丁 '), '甲\n乙 丙\n丁');
 assert.equal(cleanText('甲\\r\\n乙\\t丙\\r丁'), '甲\n乙 丙\n丁');
 assert.equal(cleanText(null), '');
});
test('missing and nonfinite deltas stay missing while actual zero remains zero', () => {
 for (const raw of [null, undefined, '', 'NaN', 'Infinity']) assert.equal(elementDelta({ delta: raw }, 'mom', 'unit'), null);
 assert.equal(elementDelta({ delta: '0' }, 'mom', 'unit'), 0);
 assert.equal(elementDelta({ delta: '9' }, 'yoy', 'unit'), null);
 assert.equal(elementDelta({ delta: '9', comparisons: { mom: { total: { delta: null } } } }, 'mom', 'total'), null);
 assert.equal(elementDelta({ delta: '9', comparisons: { mom: { total: { delta: '-3' } } } }, 'mom', 'total'), -3);
});
test('unknown delta invalidates later cumulative levels rather than assuming zero', () => {
 assert.deepEqual(waterfallBottoms(10, [2, -3, 0]), [10, 9, 9]);
 assert.deepEqual(waterfallBottoms(10, [2, null, -3]), [10, null, null]);
});
test('each terminal task notification points to the matching business page', () => {
 for (const [kind, page] of [['report', 'reports'], ['kb', 'knowledge'], ['data_parse', 'business'], ['template_parse', 'templates'], ['vector_switch', 'models']]) {
  for (const status of ['SUCCEEDED', 'DEGRADED', 'FAILED']) assert.equal(jobNotification({ kind, status }).page, page);
 }
 assert.equal(jobNotification({ kind: 'kb', status: 'SUCCEEDED' }).title, '知识库构建完成');
 assert.equal(jobNotification({ kind: 'report', status: 'FAILED' }).title, '报告任务未完成');
 assert.equal(jobNotification({ kind: 'kb', status: 'RUNNING' }), null);
 assert.equal(jobNotification({ kind: 'unknown', status: 'SUCCEEDED' }), null);
});
