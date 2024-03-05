# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
import random
import re

from odoo import api, models, fields, _
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.tools import text_from_html
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.tools.translate import html_translate


class Tintuc(models.Model):
    _name = 'tintuc.tintuc'
    _description = 'Tin tức'
    _inherit = [
        'mail.thread',
        'website.seo.metadata',
        'website.multi.mixin',
        'website.cover_properties.mixin',
        'website.searchable.mixin',
    ]
    _order = 'name'

    name = fields.Char('Tên tin tức', required=True, translate=True)
    subtitle = fields.Char('Phụ đề tin tức', translate=True)
    active = fields.Boolean('Active', default=True)
    content = fields.Html('Content', translate=html_translate, sanitize=False)
    # blog_post_ids = fields.One2many('blog.post', 'blog_id', 'Blog Posts')
    tintuc_post_ids = fields.One2many('tintuc.post', 'tintuc_id', 'Tin tuc Posts' )
    # blog_post_count = fields.Integer("Posts", compute='_compute_blog_post_count')
    tintuc_post_count = fields.Integer("Posts", compute='_compute_tintuc_post_count')

    @api.depends('tintuc_post_ids')
    def _compute_tintuc_post_count(self):
        for record in self:
            record.tintuc_post_count = len(record.tintuc_post_ids)

    def write(self, vals):
        res = super(Tintuc, self).write(vals)
        if 'active' in vals:
            # archiving/unarchiving a blog does it on its posts, too
            post_ids = self.env['tintuc.post'].with_context(active_test=False).search([
                ('tintuc_id', 'in', self.ids)
            ])
            for tintuc_post in post_ids:
                tintuc_post.active = vals['active']
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *, parent_id=False, subtype_id=False, **kwargs):
        """ Temporary workaround to avoid spam. If someone replies on a channel
        through the 'Presentation Published' email, it should be considered as a
        note as we don't want all channel followers to be notified of this answer. """
        self.ensure_one()
        if parent_id:
            parent_message = self.env['mail.message'].sudo().browse(parent_id)
            if parent_message.subtype_id and parent_message.subtype_id == self.env.ref('website_tintuc.mt_tintuc_tintuc_published'):
                subtype_id = self.env.ref('mail.mt_note').id
        return super(Tintuc, self).message_post(parent_id=parent_id, subtype_id=subtype_id, **kwargs)

    def all_tags(self, join=False, min_limit=1):
        TintucTag = self.env['tintuc.tag']
        req = """
            SELECT
                p.tintuc_id, count(*), r.tintuc_tag_id
            FROM
                tintuc_post_tintuc_tag_rel r
                    join tintuc_post p on r.tintuc_post_id=p.id
            WHERE
                p.tintuc_id in %s
            GROUP BY
                p.tintuc_id,
                r.tintuc_tag_id
            ORDER BY
                count(*) DESC
        """
        self._cr.execute(req, [tuple(self.ids)])
        tag_by_tintuc = {i.id: [] for i in self}
        all_tags = set()
        for tintuc_id, freq, tag_id in self._cr.fetchall():
            if freq >= min_limit:
                if join:
                    all_tags.add(tag_id)
                else:
                    tag_by_tintuc[tintuc_id].append(tag_id)

        if join:
            return TintucTag.browse(all_tags)

        for tintuc_id in tag_by_tintuc:
            tag_by_tintuc[tintuc_id] = TintucTag.browse(tag_by_tintuc[tintuc_id])

        return tag_by_tintuc

    @api.model
    def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        search_fields = ['name']
        fetch_fields = ['id', 'name']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'url', 'type': 'text', 'truncate': False},
        }
        if with_description:
            search_fields.append('subtitle')
            fetch_fields.append('subtitle')
            mapping['description'] = {'name': 'subtitle', 'type': 'text', 'match': True}
        return {
            'model': 'tintuc.tintuc',
            'base_domain': [website.website_domain()],
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-rss-square',
            'order': 'name desc, id desc' if 'name desc' in order else 'name asc, id desc',
        }

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)
        for data in results_data:
            data['url'] = '/tintuc/%s' % data['id']
        return results_data

class TintucTagCategory(models.Model):
    _name = 'tintuc.tag.category'
    _description = 'Tin tuc Tag Category'
    _order = 'name'

    name = fields.Char('Name', required=True, translate=True)
    tag_ids = fields.One2many('tintuc.tag', 'category_id', string='Tags')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag category already exists !"),
    ]


class TintucTag(models.Model):
    _name = 'tintuc.tag'
    _description = 'Tin tuc Tag'
    _inherit = ['website.seo.metadata']
    _order = 'name'

    name = fields.Char('Name', required=True, translate=True)
    category_id = fields.Many2one('tintuc.tag.category', 'Category', index=True)
    post_ids = fields.Many2many('tintuc.post', string='Posts')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class TintucPost(models.Model):
    _name = "tintuc.post"
    _description = "Tin tuc Post"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.published.multi.mixin',
        'website.cover_properties.mixin', 'website.searchable.mixin']
    _order = 'id DESC'
    _mail_post_access = 'read'

    def _compute_website_url(self):
        super(TintucPost, self)._compute_website_url()
        for tintuc_post in self:
            tintuc_post.website_url = "/tintuc/%s/%s" % (slug(tintuc_post.tintuc_id), slug(tintuc_post))

    def _default_content(self):
        return '''
            <p class="o_default_snippet_text">''' + _("Start writing here...") + '''</p>
        '''
    name = fields.Char('Title', required=True, translate=True, default='')
    subtitle = fields.Char('Sub Title', translate=True)
    author_id = fields.Many2one('res.partner', 'Author', default=lambda self: self.env.user.partner_id)
    author_avatar = fields.Binary(related='author_id.image_128', string="Avatar", readonly=False)
    author_name = fields.Char(related='author_id.display_name', string="Author Name", readonly=False, store=True)
    active = fields.Boolean('Active', default=True)
    tintuc_id = fields.Many2one('tintuc.tintuc', 'Tin tuc', required=True, ondelete='cascade')
    tag_ids = fields.Many2many('tintuc.tag', string='Tags')
    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False)
    teaser = fields.Text('Teaser', compute='_compute_teaser', inverse='_set_teaser')
    teaser_manual = fields.Text(string='Teaser Content')
    image_350 = fields.Image("Image", max_width=350, max_height=158, store=True)

    website_message_ids = fields.One2many(domain=lambda self: [('model', '=', self._name), ('message_type', '=', 'comment')])

    # creation / update stuff
    create_date = fields.Datetime('Created on', index=True, readonly=True)
    published_date = fields.Datetime('Published Date')
    post_date = fields.Datetime('Publishing date', compute='_compute_post_date', inverse='_set_post_date', store=True,
                                help="The tin tuc post will be visible for your visitors as of this date on the website if it is set as published.")
    create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True)
    write_date = fields.Datetime('Last Updated on', index=True, readonly=True)
    write_uid = fields.Many2one('res.users', 'Last Contributor', index=True, readonly=True)
    visits = fields.Integer('No of Views', copy=False, default=0)
    website_id = fields.Many2one(related='tintuc_id.website_id', readonly=True, store=True)

    @api.depends('content', 'teaser_manual')
    def _compute_teaser(self):
        for tintuc_post in self:
            if tintuc_post.teaser_manual:
                tintuc_post.teaser = tintuc_post.teaser_manual
            else:
                content = text_from_html(tintuc_post.content)
                content = re.sub('\\s+', ' ', content).strip()
                tintuc_post.teaser = content[:200] + '...'

    def _set_teaser(self):
        for tintuc_post in self:
            tintuc_post.teaser_manual = tintuc_post.teaser

    @api.depends('create_date', 'published_date')
    def _compute_post_date(self):
        for tintuc_post in self:
            if tintuc_post.published_date:
                tintuc_post.post_date = tintuc_post.published_date
            else:
                tintuc_post.post_date = tintuc_post.create_date

    def _set_post_date(self):
        for tintuc_post in self:
            tintuc_post.published_date = tintuc_post.post_date
            if not tintuc_post.published_date:
                tintuc_post._write(dict(post_date=tintuc_post.create_date)) # dont trigger inverse function

    def _check_for_publication(self, vals):
        if vals.get('is_published'):
            for post in self.filtered(lambda p: p.active):
                post.tintuc_id.message_post_with_view(
                    'website_tintuc.tintuc_post_template_new_post',
                    subject=post.name,
                    values={'post': post},
                    subtype_id=self.env['ir.model.data']._xmlid_to_res_id('website_tintuc.mt_tintuc_tintuc_published'))
            return True
        return False

    @api.model
    def create(self, vals):
        post_id = super(TintucPost, self.with_context(mail_create_nolog=True)).create(vals)
        post_id._check_for_publication(vals)
        return post_id

    def write(self, vals):
        result = True
        # archiving a blog post, unpublished the blog post
        if 'active' in vals and not vals['active']:
            vals['is_published'] = False
        for post in self:
            copy_vals = dict(vals)
            published_in_vals = set(vals.keys()) & {'is_published', 'website_published'}
            if (published_in_vals and 'published_date' not in vals and
                    (not post.published_date or post.published_date <= fields.Datetime.now())):
                copy_vals['published_date'] = vals[list(published_in_vals)[0]] and fields.Datetime.now() or False
            result &= super(TintucPost, post).write(copy_vals)
        self._check_for_publication(vals)
        return result

    @api.returns('self', lambda value: value.id)
    def copy_data(self, default=None):
        self.ensure_one()
        name = _("%s (copy)", self.name)
        default = dict(default or {}, name=name)
        return super(TintucPost, self).copy_data(default)

    def get_access_action(self, access_uid=None):
        """ Instead of the classic form view, redirect to the post on website
        directly if user is an employee or if the post is published. """
        self.ensure_one()
        user = access_uid and self.env['res.users'].sudo().browse(access_uid) or self.env.user
        if user.share and not self.sudo().website_published:
            return super(TintucPost, self).get_access_action(access_uid)
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'self',
            'target_type': 'public',
            'res_id': self.id,
        }

    def _notify_get_groups(self, msg_vals=None):
        """ Add access button to everyone if the document is published. """
        groups = super(TintucPost, self)._notify_get_groups(msg_vals=msg_vals)

        if self.website_published:
            for group_name, group_method, group_data in groups:
                group_data['has_button_access'] = True

        return groups

    def _notify_record_by_inbox(self, message, recipients_data, msg_vals=False, **kwargs):
        """ Override to avoid keeping all notified recipients of a comment.
        We avoid tracking needaction on post comments. Only emails should be
        sufficient. """
        if msg_vals.get('message_type', message.message_type) == 'comment':
            return
        return super(TintucPost, self)._notify_record_by_inbox(message, recipients_data, msg_vals=msg_vals, **kwargs)

    def _default_website_meta(self):
        res = super(TintucPost, self)._default_website_meta()
        res['default_opengraph']['og:description'] = res['default_twitter']['twitter:description'] = self.subtitle
        res['default_opengraph']['og:type'] = 'article'
        res['default_opengraph']['article:published_time'] = self.post_date
        res['default_opengraph']['article:modified_time'] = self.write_date
        res['default_opengraph']['article:tag'] = self.tag_ids.mapped('name')
        # background-image might contain single quotes eg `url('/my/url')`
        res['default_opengraph']['og:image'] = res['default_twitter']['twitter:image'] = json_scriptsafe.loads(self.cover_properties).get('background-image', 'none')[4:-1].strip("'")
        res['default_opengraph']['og:title'] = res['default_twitter']['twitter:title'] = self.name
        res['default_meta_description'] = self.subtitle
        return res

    @api.model
    def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        tintuc = options.get('tintuc')
        tags = options.get('tag')
        date_begin = options.get('date_begin')
        date_end = options.get('date_end')
        state = options.get('state')
        domain = [website.website_domain()]
        if tintuc:
            domain.append([('tintuc_id', '=', unslug(tintuc)[1])])
        if tags:
            active_tag_ids = [unslug(tag)[1] for tag in tags.split(',')] or []
            if active_tag_ids:
                domain.append([('tag_ids', 'in', active_tag_ids)])
        if date_begin and date_end:
            domain.append([("post_date", ">=", date_begin), ("post_date", "<=", date_end)])
        if self.env.user.has_group('website.group_website_designer'):
            if state == "published":
                domain.append([("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())])
            elif state == "unpublished":
                domain.append(['|', ("website_published", "=", False), ("post_date", ">", fields.Datetime.now())])
        else:
            domain.append([("post_date", "<=", fields.Datetime.now())])
        search_fields = ['name', 'author_name']
        def search_in_tags(env, search_term):
            tags_like_search = env['tintuc.tag'].search([('name', 'ilike', search_term)])
            return [('tag_ids', 'in', tags_like_search.ids)]
        fetch_fields = ['name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_description:
            search_fields.append('content')
            fetch_fields.append('content')
            mapping['description'] = {'name': 'content', 'type': 'text', 'html': True, 'match': True}
        if with_date:
            fetch_fields.append('published_date')
            mapping['detail'] = {'name': 'published_date', 'type': 'date'}
        return {
            'model': 'tintuc.post',
            'base_domain': domain,
            'search_fields': search_fields,
            'search_extra': search_in_tags,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-rss',
        }
