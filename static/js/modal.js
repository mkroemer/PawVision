// PawVision Universal Modal System
// Generic modal system that can handle any type of modal

/**
 * Universal Modal System
 * Handles all types of modals: confirmations, forms, alerts, custom content
 */
const Modal = {
    activeModals: new Map(),
    modalCounter: 0,

    /**
     * Create and show a modal
     * @param {Object} config - Modal configuration
     * @returns {string} Modal ID for future reference
     */
    show(config) {
        const {
            id = `modal-${++this.modalCounter}`,
            title = '',
            content = '',
            type = 'info', // 'info', 'confirm', 'alert', 'form', 'custom'
            size = 'medium', // 'small', 'medium', 'large', 'fullscreen'
            buttons = [],
            closable = true,
            backdrop = true, // Close on backdrop click
            keyboard = true, // Close on ESC key
            onShow = null,
            onHide = null,
            className = ''
        } = config;

        // Remove existing modal with same ID
        this.hide(id);

        const modal = this.createModal({
            id, title, content, type, size, buttons, 
            closable, backdrop, keyboard, className
        });

        // Add to DOM
        document.body.appendChild(modal);
        
        // Store modal info
        this.activeModals.set(id, {
            element: modal,
            config,
            onShow,
            onHide
        });

        // Show modal with animation
        requestAnimationFrame(() => {
            modal.classList.add('modal-show');
            document.body.classList.add('modal-open');
        });

        // Setup event listeners
        this.setupModalEvents(id);

        // Call onShow callback
        if (onShow) onShow(id);

        return id;
    },

    /**
     * Hide and remove a modal
     * @param {string} id - Modal ID
     */
    hide(id) {
        const modalInfo = this.activeModals.get(id);
        if (!modalInfo) return;

        const modal = modalInfo.element;
        
        // Call onHide callback
        if (modalInfo.onHide) modalInfo.onHide(id);

        // Hide with animation
        modal.classList.remove('modal-show');
        
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
            this.activeModals.delete(id);
            
            // Remove body class if no modals are active
            if (this.activeModals.size === 0) {
                document.body.classList.remove('modal-open');
            }
        }, 300);
    },

    /**
     * Create modal DOM element
     */
    createModal({ id, title, content, type, size, buttons, closable, className }) {
        const modal = document.createElement('div');
        modal.className = `modal modal-${type} modal-${size} ${className}`;
        modal.id = id;

        const modalDialog = document.createElement('div');
        modalDialog.className = 'modal-dialog';

        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';

        // Header
        if (title || closable) {
            const header = document.createElement('div');
            header.className = 'modal-header';
            
            if (title) {
                const titleElement = document.createElement('h4');
                titleElement.className = 'modal-title';
                titleElement.textContent = title;
                header.appendChild(titleElement);
            }
            
            if (closable) {
                const closeBtn = document.createElement('button');
                closeBtn.className = 'modal-close';
                closeBtn.innerHTML = '&times;';
                closeBtn.onclick = () => this.hide(id);
                header.appendChild(closeBtn);
            }
            
            modalContent.appendChild(header);
        }

        // Body
        const body = document.createElement('div');
        body.className = 'modal-body';
        
        if (typeof content === 'string') {
            body.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            body.appendChild(content);
        }
        
        modalContent.appendChild(body);

        // Footer with buttons
        if (buttons && buttons.length > 0) {
            const footer = document.createElement('div');
            footer.className = 'modal-footer';
            
            buttons.forEach(btn => {
                const button = document.createElement('button');
                button.className = `btn ${btn.className || 'btn-secondary'}`;
                button.textContent = btn.text;
                
                if (btn.onClick) {
                    button.onclick = () => {
                        const result = btn.onClick(id);
                        if (result !== false) this.hide(id);
                    };
                }
                
                footer.appendChild(button);
            });
            
            modalContent.appendChild(footer);
        }

        modalDialog.appendChild(modalContent);
        modal.appendChild(modalDialog);
        
        return modal;
    },

    /**
     * Setup event listeners for a modal
     */
    setupModalEvents(id) {
        const modalInfo = this.activeModals.get(id);
        if (!modalInfo) return;

        const modal = modalInfo.element;
        const { backdrop, keyboard } = modalInfo.config;

        // Backdrop click
        if (backdrop) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hide(id);
                }
            });
        }

        // Keyboard events
        if (keyboard) {
            const keyHandler = (e) => {
                if (e.key === 'Escape') {
                    this.hide(id);
                    document.removeEventListener('keydown', keyHandler);
                }
            };
            document.addEventListener('keydown', keyHandler);
        }
    },

    /**
     * Convenience method for confirmation dialog
     */
    confirm(options) {
        const {
            title = 'Confirm',
            message = 'Are you sure?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            onConfirm = null,
            onCancel = null,
            type = 'warning'
        } = options;

        return this.show({
            title,
            content: `<p>${message}</p>`,
            type,
            buttons: [
                {
                    text: cancelText,
                    className: 'btn-secondary',
                    onClick: (id) => {
                        if (onCancel) onCancel();
                        return true; // Close modal
                    }
                },
                {
                    text: confirmText,
                    className: 'btn-primary',
                    onClick: (id) => {
                        if (onConfirm) onConfirm();
                        return true; // Close modal
                    }
                }
            ]
        });
    },

    /**
     * Convenience method for alert dialog
     */
    alert(options) {
        const {
            title = 'Alert',
            message = '',
            type = 'info',
            buttonText = 'OK',
            onClose = null
        } = options;

        return this.show({
            title,
            content: `<p>${message}</p>`,
            type,
            buttons: [
                {
                    text: buttonText,
                    className: 'btn-primary',
                    onClick: (id) => {
                        if (onClose) onClose();
                        return true;
                    }
                }
            ]
        });
    },

    /**
     * Convenience method for form modal
     */
    form(options) {
        const {
            title = 'Form',
            fields = [],
            submitText = 'Submit',
            cancelText = 'Cancel',
            onSubmit = null,
            onCancel = null
        } = options;

        // Create form HTML
        let formHTML = '<form class="modal-form">';
        fields.forEach(field => {
            formHTML += `
                <div class="form-group">
                    <label for="${field.name}">${field.label}</label>
                    <input 
                        type="${field.type || 'text'}" 
                        id="${field.name}" 
                        name="${field.name}" 
                        value="${field.value || ''}"
                        ${field.required ? 'required' : ''}
                        ${field.placeholder ? `placeholder="${field.placeholder}"` : ''}
                    />
                </div>
            `;
        });
        formHTML += '</form>';

        return this.show({
            title,
            content: formHTML,
            type: 'form',
            buttons: [
                {
                    text: cancelText,
                    className: 'btn-secondary',
                    onClick: (id) => {
                        if (onCancel) onCancel();
                        return true;
                    }
                },
                {
                    text: submitText,
                    className: 'btn-primary',
                    onClick: (id) => {
                        const form = document.querySelector(`#${id} .modal-form`);
                        const formData = new FormData(form);
                        const data = Object.fromEntries(formData.entries());
                        
                        if (onSubmit) {
                            const result = onSubmit(data);
                            return result !== false; // Close modal unless explicitly prevented
                        }
                        return true;
                    }
                }
            ]
        });
    },

    /**
     * Hide all modals
     */
    hideAll() {
        Array.from(this.activeModals.keys()).forEach(id => this.hide(id));
    },

    /**
     * Get active modal count
     */
    count() {
        return this.activeModals.size;
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Modal;
}
