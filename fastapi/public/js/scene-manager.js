/**
 * TheSevenTactics — SceneManager
 * Unity-style stack-based scene management
 */

const SceneManager = {
    _scenes: {},
    _stack: [],
    _container: null,

    init(container) {
        this._container = container;
        this._scenes = {};
        this._stack = [];
    },

    register(name, module) {
        this._scenes[name] = module;
    },

    async push(name, data) {
        const module = this._scenes[name];
        if (!module) { console.error(`[SceneManager] Scene not found: ${name}`); return; }

        const current = this._peek();
        if (current) {
            if (current.module.onPause) current.module.onPause();
            current.el.classList.remove('scene-active');
            current.el.classList.add('scene-hidden');
        }

        const el = this._createElement(name);
        this._stack.push({ name, module, el });
        await module.mount(el, data);
        console.log(`[SceneManager] push -> ${name} (depth: ${this._stack.length})`);
    },

    async pop(data) {
        if (this._stack.length <= 1) { console.warn('[SceneManager] Cannot pop last scene'); return; }

        const popped = this._stack.pop();
        if (popped.module.unmount) popped.module.unmount();
        popped.el.remove();

        const current = this._peek();
        if (current) {
            current.el.classList.remove('scene-hidden');
            current.el.classList.add('scene-active');
            if (current.module.onResume) current.module.onResume(data);
        }
        console.log(`[SceneManager] pop <- ${popped.name} (depth: ${this._stack.length})`);
    },

    async replace(name, data) {
        const module = this._scenes[name];
        if (!module) { console.error(`[SceneManager] Scene not found: ${name}`); return; }

        const current = this._peek();
        if (current) {
            if (current.module.unmount) current.module.unmount();
            current.el.remove();
            this._stack.pop();
        }

        const el = this._createElement(name);
        this._stack.push({ name, module, el });
        await module.mount(el, data);
        console.log(`[SceneManager] replace -> ${name} (depth: ${this._stack.length})`);
    },

    async resetTo(name, data) {
        while (this._stack.length > 0) {
            const entry = this._stack.pop();
            if (entry.module.unmount) entry.module.unmount();
            entry.el.remove();
        }
        await this.push(name, data);
    },

    current() {
        const top = this._peek();
        return top ? top.name : null;
    },

    depth() { return this._stack.length; },

    _peek() {
        return this._stack.length > 0 ? this._stack[this._stack.length - 1] : null;
    },

    _createElement(name) {
        const el = document.createElement('div');
        el.className = 'scene scene-active';
        el.dataset.scene = name;
        this._container.appendChild(el);
        return el;
    },
};

export { SceneManager };
