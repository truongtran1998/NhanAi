odoo.define('website_tintuc.wysiwyg', function (require) {
'use strict';


const Wysiwyg = require('web_editor.wysiwyg');
require('website.editor.snippets.options');

Wysiwyg.include({
    custom_events: Object.assign({}, Wysiwyg.prototype.custom_events, {
        'set_tintuc_post_updated_tags': '_onSetTintucPostUpdatedTags',
    }),

    /**
     * @override
     */
    init() {
        this._super(...arguments);
        this.tintucTagsPerTintucPost = {};
    },
    /**
     * @override
     */
    async start() {
        await this._super(...arguments);
        $('.js_tweet, .js_comment').off('mouseup').trigger('mousedown');
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    async _saveViewBlocks() {
        const ret = await this._super(...arguments);
        await this._saveTintucTags(); // Note: important to be called after save otherwise cleanForSave is not called before
        return ret;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Saves the blog tags in the database.
     *
     * @private
     */
    async _saveTintucTags() {
        for (const [key, tags] of Object.entries(this.tintucTagsPerTintucPost)) {
            const proms = tags.filter(tag => typeof tag.id === 'string').map(tag => {
                return this._rpc({
                    model: 'tintuc.tag',
                    method: 'create',
                    args: [{
                        'name': tag.name,
                    }],
                });
            });
            const createdIDs = await Promise.all(proms);

            await this._rpc({
                model: 'tintuc.post',
                method: 'write',
                args: [parseInt(key), {
                    'tag_ids': [[6, 0, tags.filter(tag => typeof tag.id === 'number').map(tag => tag.id).concat(createdIDs)]],
                }],
            });
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onSetTintucPostUpdatedTags: function (ev) {
        this.tintucTagsPerTintucPost[ev.data.tintucPostID] = ev.data.tags;
    },
});

});
