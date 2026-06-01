const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync('index.html', 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/)[1];
const capturedRequests = [];
let failFirstChat = true;

function element(id = '') {
  return {
    id,
    value: '',
    textContent: '',
    innerHTML: '',
    className: '',
    style: { setProperty() {}, getPropertyValue() { return ''; } },
    classList: { add() {}, remove() {} },
    children: [],
    disabled: false,
    scrollTop: 0,
    scrollHeight: 0,
    appendChild(child) { this.children.push(child); return child; },
    addEventListener() {},
    querySelector() { return element('query'); },
    setAttribute() {},
    hasAttribute() { return false; },
    toggleAttribute() {},
    focus() {},
    form: { requestSubmit() {} },
  };
}

const elements = new Map([
  ['chatLoader', element('chatLoader')],
  ['chatForm', element('chatForm')],
  ['chatInput', element('chatInput')],
  ['chatSend', element('chatSend')],
  ['chatMessages', element('chatMessages')],
  ['contextPill', element('contextPill')],
  ['ideaList', element('ideaList')],
  ['ideaCount', element('ideaCount')],
]);

const idea = {
  id: 'ai-harness',
  title: 'The "Harness" Problem: Why Cloud AI Integrations Are Your Weakest Link',
  date: '2026-01-01',
  summary: 'AI harness cloud integrations local AI privacy workflow orchestration',
  tags: ['AI', 'harness', 'cloud'],
  file: 'ideas/posts/ai-harness.md',
};
const markdown = 'An AI harness is the control layer around cloud AI integrations. It routes tasks, protects privacy, preserves context, and lets teams use AI without giving up governance.';

const context = {
  console: { debug() {}, log() {}, error() {} },
  window: { location: { search: '?debug=chat', hostname: 'mac-studio.magicdns' } },
  document: {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element(id));
      return elements.get(id);
    },
    createElement() { return element('created'); },
    querySelectorAll() { return []; },
    addEventListener(type, handler) {
      if (type === 'DOMContentLoaded') handler();
    },
  },
  IntersectionObserver: function() { this.observe = function() {}; this.unobserve = function() {}; },
  fetch: async (url, options = {}) => {
    if (url === 'ideas/index.json') return { ok: true, json: async () => [idea] };
    if (url === idea.file) return { ok: true, text: async () => markdown };
    if (String(url).includes('/gradio_api/call/chat') && options.method === 'POST') {
      capturedRequests.push(JSON.parse(options.body));
      if (failFirstChat) {
        failFirstChat = false;
        return { ok: false, json: async () => ({}) };
      }
      return { ok: true, json: async () => ({ event_id: String(capturedRequests.length) }) };
    }
    if (String(url).includes('/gradio_api/call/chat_with_history/') || String(url).includes('/gradio_api/call/chat/')) {
      return { ok: true, text: async () => 'data: ["assistant reply"]\n' };
    }
    throw new Error(`Unexpected fetch ${url}`);
  },
  URLSearchParams,
  setTimeout,
  clearTimeout,
};
context.window.window = context.window;
context.window.document = context.document;
context.window.fetch = context.fetch;
context.window.console = context.console;
context.window.IntersectionObserver = context.IntersectionObserver;

async function submit(message) {
  elements.get('chatInput').value = message;
  await context.handleChatSubmit({ preventDefault() {} });
}

(async () => {
  vm.createContext(context);
  vm.runInContext(script, context);
  await new Promise(resolve => setImmediate(resolve));

  await submit('tell me about AI harness');
  await submit('tell me about AI harness');

  assert.strictEqual(capturedRequests.length, 2, 'expected two chat POSTs');
  const [first, second] = capturedRequests;
  assert(first.data[0].includes('<context'), 'first attempted payload should include hidden context');
  assert(second.data[0].includes('<context'), 'retry after failed context send should include hidden context again');
  assert.strictEqual(second.data[1].filter(turn => String(turn.content).includes('<context')).length, 0, 'failed context send should not create phantom history');

  console.log(JSON.stringify({
    firstCurrentHasContext: first.data[0].includes('<context'),
    secondCurrentHasContext: second.data[0].includes('<context'),
    secondHistoryContextCount: second.data[1].filter(turn => String(turn.content).includes('<context')).length,
  }, null, 2));
})().catch(error => {
  console.error(error);
  process.exit(1);
});
