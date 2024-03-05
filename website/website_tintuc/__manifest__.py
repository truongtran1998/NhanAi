# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Tin tức',
    'category': 'Website/Website',
    'sequence': 201,
    'website': 'http://www.benhviennhanai.vn',
    'summary': 'Publish news',
    'version': '1.1',
    'description': "",
    'depends': ['website_mail', 'website_partner', 'im_livechat'],
    'data': [
        # 'data/mail_data.xml',
        # 'data/mail_templates.xml',
        # 'data/website_blog_data.xml',
        # 'data/blog_snippet_template_data.xml',
        'data/website_data.xml',
        'data/website_tintuc_data.xml',
        'views/website_tintuc_views.xml',
        'views/website_tintuc_components.xml',
        'views/website_tintuc_posts_loop.xml',
        'views/website_tintuc_templates.xml',
        # 'views/website_templates.xml',
        'views/webclient_templates.xml',
        # 'views/snippets/snippets.xml',
        # 'views/snippets/s_tintuc_posts.xml',
        'security/ir.model.access.csv',
        # 'security/website_blog_security.xml',
        'security/website_tintuc_security.xml',
    ],
    'demo': [
        # 'data/website_blog_demo.xml'
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'assets': {
        'website.assets_wysiwyg': [
            'website_tintuc/static/src/js/options.js',
            'website_tintuc/static/src/js/wysiwyg.js',
            # 'website_blog/static/src/snippets/s_blog_posts/options.js',
        ],
        'website.assets_editor': [
            'website_tintuc/static/src/js/website_tintuc.editor.js',
            # 'website_tintuc/static/src/js/tours/website_tintuc.js',
        ],
        'web.assets_frontend': [
            'website_tintuc/static/src/scss/website_tintuc.scss',
            'website_tintuc/static/src/js/contentshare.js',
            'website_tintuc/static/src/js/website_tintuc.js',
        ],
    },
    'license': 'LGPL-3',
}
