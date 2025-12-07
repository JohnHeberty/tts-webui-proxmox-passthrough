// Jest setup file
require('@testing-library/jest-dom');

// Mock Bootstrap Toast
global.bootstrap = {
  Toast: class {
    constructor(element) {
      this.element = element;
    }
    show() {
      this.element.classList.add('show');
    }
    hide() {
      this.element.classList.remove('show');
    }
  },
  Modal: class {
    constructor(element) {
      this.element = element;
    }
    show() {
      this.element.style.display = 'block';
    }
    hide() {
      this.element.style.display = 'none';
    }
    static getInstance(element) {
      return new this(element);
    }
  }
};

// Mock fetch globally
global.fetch = jest.fn();

// Mock AbortController
global.AbortController = class {
  constructor() {
    this.signal = { aborted: false };
  }
  abort() {
    this.signal.aborted = true;
  }
};

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  fetch.mockClear();
});
