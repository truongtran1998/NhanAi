# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import url_for


class Website(models.Model):
    _inherit = "website"

    @api.model
    def page_search_dependencies(self, page_id=False):
        dep = super(Website, self).page_search_dependencies(page_id=page_id)

        page = self.env['website.page'].browse(int(page_id))
        path = page.url

        dom = [
            ('content', 'ilike', path)
        ]
        posts = self.env['tintuc.post'].search(dom)
        if posts:
            page_key = _('Tin tuc Post')
            if len(posts) > 1:
                page_key = _('Tin tuc Posts')
            dep[page_key] = []
        for p in posts:
            dep[page_key].append({
                'text': _('News Post <b>%s</b> seems to have a link to this page !', p.name),
                'item': p.name,
                'link': p.website_url,
            })

        return dep

    @api.model
    def page_search_key_dependencies(self, page_id=False):
        dep = super(Website, self).page_search_key_dependencies(page_id=page_id)

        page = self.env['website.page'].browse(int(page_id))
        key = page.key

        dom = [
            ('content', 'ilike', key)
        ]
        posts = self.env['tintuc.post'].search(dom)
        if posts:
            page_key = _('Tin tuc Post')
            if len(posts) > 1:
                page_key = _('Tin tuc Posts')
            dep[page_key] = []
        for p in posts:
            dep[page_key].append({
                'text': _('News Post <b>%s</b> seems to be calling this file !', p.name),
                'item': p.name,
                'link': p.website_url,
            })

        return dep

    def get_suggested_controllers(self):
        suggested_controllers = super(Website, self).get_suggested_controllers()
        suggested_controllers.append((_('Tin tuc'), url_for('/tintuc'), 'website_tintuc'))
        return suggested_controllers

    def configurator_set_menu_links(self, menu_company, module_data):
        tintucs = module_data.get('#tintuc', [])
        for idx, tintuc in enumerate(tintucs):
            new_tintuc = self.env['tintuc.tintuc'].create({
                'name': tintuc['name'],
                'website_id': self.id,
            })
            tintuc_menu_values = {
                'name': tintuc['name'],
                'url': '/tintuc/%s' % new_tintuc.id,
                'sequence': tintuc['sequence'],
                'parent_id': menu_company.id if menu_company else self.menu_id.id,
                'website_id': self.id,
            }
            if idx == 0:
                tintuc_menu = self.env['website.menu'].search([('url', '=', '/tintuc'), ('website_id', '=', self.id)])
                tintuc_menu.write(tintuc_menu_values)
            else:
                self.env['website.menu'].create(tintuc_menu_values)
        super().configurator_set_menu_links(menu_company, module_data)

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        if search_type in ['tintucs', 'tintucs_only', 'all']:
            result.append(self.env['tintuc.tintuc']._search_get_detail(self, order, options))
        if search_type in ['tintucs', 'tintuc_posts_only', 'all']:
            result.append(self.env['tintuc.post']._search_get_detail(self, order, options))
        return result