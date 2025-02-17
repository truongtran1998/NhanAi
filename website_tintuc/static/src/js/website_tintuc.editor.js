odoo.define('website_tintuc.new_tintuc_post', function (require) {
'use strict';

var core = require('web.core');
var wUtils = require('website.utils');
var WebsiteNewMenu = require('website.newMenu');

var _t = core._t;

WebsiteNewMenu.include({
    actions: _.extend({}, WebsiteNewMenu.prototype.actions || {}, {
        new_tintuc_post: '_createNewTintucPost',
    }),

    //--------------------------------------------------------------------------
    // Actions
    //--------------------------------------------------------------------------

    /**
     * Asks the user information about a new blog post to create, then creates
     * it and redirects the user to this new post.
     *
     * @private
     * @returns {Promise} Unresolved if there is a redirection
     */
    _createNewTintucPost: function () {
        return this._rpc({
            model: 'tintuc.tintuc',
            method: 'search_read',
            args: [wUtils.websiteDomain(this), ['name']],
        }).then(function (tintucs) {
            if (tintucs.length === 1) {
                document.location = '/tintuc/' + tintucs[0]['id'] + '/post/new';
                return new Promise(function () {});
            } else if (tintucs.length > 1) {
                return wUtils.prompt({
                    id: 'editor_new_tintuc',
                    window_title: _t("New Tin Tuc Post"),
                    select: _t("Select Tin Tuc"),
                    init: function (field) {
                        return _.map(tintucs, function (tintuc) {
                            return [tintuc['id'], tintuc['name']];
                        });
                    },
                }).then(function (result) {
                    var tintuc_id = result.val;
                    if (!tintuc_id) {
                        return;
                    }
                    document.location = '/tintuc/' + tintuc_id + '/post/new';
                    return new Promise(function () {});
                });
            }
        });
    },
});
});
