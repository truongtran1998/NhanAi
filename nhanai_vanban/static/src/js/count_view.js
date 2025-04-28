odoo.define('nhanai_vanban.ControllerViewTracker', function (require) {
'use strict';

const FormController = require('web.FormController');

const ViewTrackingFormController = FormController.include({
        update: function (params, options) {
            console.log("Form view updated!");
            console.log("-------------------", params);
            if (params.currentId) {
                // Gửi request tới server để tăng số đếm
                this._rpc({
                    model: 'project.task',
                    method: 'increment_view_count',
                    args: [params.currentId, params.modelName],
                });
            }
            return this._super.apply(this, arguments);
        },
    });

    return ViewTrackingFormController;

});
