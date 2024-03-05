# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import werkzeug
import itertools
import pytz
import babel.dates
from collections import OrderedDict

from odoo import http, fields
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.portal.controllers.web import Home
from odoo.http import request
from odoo.osv import expression
from odoo.tools import html2plaintext
from odoo.tools.misc import get_lang
from odoo.tools import sql


class WebsiteTintuc(http.Controller):
    _tintuc_post_per_page = 12  # multiple of 2,3,4
    _post_comment_per_page = 10

    def tags_list(self, tag_ids, current_tag):
        tag_ids = list(tag_ids)  # required to avoid using the same list
        if current_tag in tag_ids:
            tag_ids.remove(current_tag)
        else:
            tag_ids.append(current_tag)
        tag_ids = request.env['tintuc.tag'].browse(tag_ids)
        return ','.join(slug(tag) for tag in tag_ids)

    def nav_list(self, tintuc=None):
        dom = tintuc and [('tintuc_id', '=', tintuc.id)] or []
        if not request.env.user.has_group('website.group_website_designer'):
            dom += [('post_date', '<=', fields.Datetime.now())]
        groups = request.env['tintuc.post']._read_group_raw(
            dom,
            ['name', 'post_date'],
            groupby=["post_date"], orderby="post_date desc")
        for group in groups:
            (r, label) = group['post_date']
            start, end = r.split('/')
            group['post_date'] = label
            group['date_begin'] = start
            group['date_end'] = end

            locale = get_lang(request.env).code
            start = pytz.UTC.localize(fields.Datetime.from_string(start))
            tzinfo = pytz.timezone(request.context.get('tz', 'utc') or 'utc')

            group['month'] = babel.dates.format_datetime(start, format='MMMM', tzinfo=tzinfo, locale=locale)
            group['year'] = babel.dates.format_datetime(start, format='yyyy', tzinfo=tzinfo, locale=locale)

        return OrderedDict((year, [m for m in months]) for year, months in itertools.groupby(groups, lambda g: g['year']))

    def _prepare_tintuc_values(self, tintucs, tintuc=False, date_begin=False, date_end=False, tags=False, state=False, page=False, search=None):
        """ Prepare all values to display the tintucs index page or one specific tintuc"""
        TintucPost = request.env['tintuc.post']
        TintucTag = request.env['tintuc.tag']

        # prepare domain
        domain = request.website.website_domain()

        if tintuc:
            domain += [('tintuc_id', '=', tintuc.id)]

        if date_begin and date_end:
            domain += [("post_date", ">=", date_begin), ("post_date", "<=", date_end)]
        active_tag_ids = tags and [unslug(tag)[1] for tag in tags.split(',')] or []
        active_tags = TintucTag
        if active_tag_ids:
            active_tags = TintucTag.browse(active_tag_ids).exists()
            fixed_tag_slug = ",".join(slug(t) for t in active_tags)
            if fixed_tag_slug != tags:
                path = request.httprequest.full_path
                new_url = path.replace("/tag/%s" % tags, fixed_tag_slug and "/tag/%s" % fixed_tag_slug or "", 1)
                if new_url != path:  # check that really replaced and avoid loop
                    return request.redirect(new_url, 301)
            domain += [('tag_ids', 'in', active_tags.ids)]

        if request.env.user.has_group('website.group_website_designer'):
            count_domain = domain + [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            published_count = TintucPost.search_count(count_domain)
            unpublished_count = TintucPost.search_count(domain) - published_count

            if state == "published":
                domain += [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            elif state == "unpublished":
                domain += ['|', ("website_published", "=", False), ("post_date", ">", fields.Datetime.now())]
        else:
            domain += [("post_date", "<=", fields.Datetime.now())]

        use_cover = request.website.is_view_active('website_tintuc.opt_tintuc_cover_post')
        fullwidth_cover = request.website.is_view_active('website_tintuc.opt_tintuc_cover_post_fullwidth_design')

        # if tintuc, we show tintuc title, if use_cover and not fullwidth_cover we need pager + latest always
        offset = (page - 1) * self._tintuc_post_per_page
        if not tintuc:
            if use_cover and not fullwidth_cover and not tags and not date_begin and not date_end:
                offset += 1

        options = {
            'displayDescription': True,
            'displayDetail': False,
            'displayExtraDetail': False,
            'displayExtraLink': False,
            'displayImage': False,
            'allowFuzzy': not request.params.get('noFuzzy'),
            'tintuc': str(tintuc.id) if tintuc else None,
            'tag': ','.join([str(id) for id in active_tags.ids]),
            'date_begin': date_begin,
            'date_end': date_end,
            'state': state,
        }
        total, details, fuzzy_search_term = request.website._search_with_fuzzy("tintuc_posts_only", search,
            limit=page * self._tintuc_post_per_page, order="is_published desc, post_date desc, id asc", options=options)
        posts = details[0].get('results', TintucPost)
        first_post = TintucPost
        if posts and not tintuc and posts[0].website_published:
            first_post = posts[0]
        posts = posts[offset:offset + self._tintuc_post_per_page]

        url_args = dict()
        if search:
            url_args["search"] = search

        if date_begin and date_end:
            url_args["date_begin"] = date_begin
            url_args["date_end"] = date_end

        pager = request.website.pager(
            url=request.httprequest.path.partition('/page/')[0],
            total=total,
            page=page,
            step=self._tintuc_post_per_page,
            url_args=url_args,
        )

        if not tintucs:
            all_tags = request.env['tintuc.tag']
        else:
            all_tags = tintucs.all_tags(join=True) if not tintuc else tintucs.all_tags().get(tintuc.id, request.env['tintuc.tag'])
        tag_category = sorted(all_tags.mapped('category_id'), key=lambda category: category.name.upper())
        other_tags = sorted(all_tags.filtered(lambda x: not x.category_id), key=lambda tag: tag.name.upper())

        # for performance prefetch the first post with the others
        post_ids = (first_post | posts).ids
        # and avoid accessing related tintucs one by one
        posts.tintuc_id

        return {
            'date_begin': date_begin,
            'date_end': date_end,
            'first_post': first_post.with_prefetch(post_ids),
            'other_tags': other_tags,
            'tag_category': tag_category,
            'nav_list': self.nav_list(),
            'tags_list': self.tags_list,
            'pager': pager,
            'posts': posts.with_prefetch(post_ids),
            'tag': tags,
            'active_tag_ids': active_tags.ids,
            'domain': domain,
            'state_info': state and {"state": state, "published": published_count, "unpublished": unpublished_count},
            'tintucs': tintucs,
            'tintuc': tintuc,
            'search': fuzzy_search_term or search,
            'search_count': total,
            'original_search': fuzzy_search_term and search,
        }

    @http.route([
        '/tintuc',
        '/tintuc/page/<int:page>',
        '/tintuc/tag/<string:tag>',
        '/tintuc/tag/<string:tag>/page/<int:page>',
        '''/tintuc/<model("tintuc.tintuc"):tintuc>''',
        '''/tintuc/<model("tintuc.tintuc"):tintuc>/page/<int:page>''',
        '''/tintuc/<model("tintuc.tintuc"):tintuc>/tag/<string:tag>''',
        '''/tintuc/<model("tintuc.tintuc"):tintuc>/tag/<string:tag>/page/<int:page>''',
    ], type='http', auth="public", website=True, sitemap=True)
    def tintuc(self, tintuc=None, tag=None, page=1, search=None, **opt):
        Tintuc = request.env['tintuc.tintuc']

        # TODO adapt in master. This is a fix for templates wrongly using the
        # 'blog_url' QueryURL which is defined below. Indeed, in the case where
        # we are rendering a blog page where no specific blog is selected we
        # define(d) that as `QueryURL('/blog', ['tag'], ...)` but then some
        # parts of the template used it like this: `blog_url(blog=XXX)` thus
        # generating an URL like "/blog?blog=blog.blog(2,)". Adding "blog" to
        # the list of params would not be right as would create "/blog/blog/2"
        # which is still wrong as we want "/blog/2". And of course the "/blog"
        # prefix in the QueryURL definition is needed in case we only specify a
        # tag via `blog_url(tab=X)` (we expect /blog/tag/X). Patching QueryURL
        # or making blog_url a custom function instead of a QueryURL instance
        # could be a solution but it was judged not stable enough. We'll do that
        # in master. Here we only support "/blog?blog=blog.blog(2,)" URLs.
        if isinstance(tintuc, str):
            tintuc = Tintuc.browse(int(re.search(r'\d+', tintuc)[0]))
            if not tintuc.exists():
                raise werkzeug.exceptions.NotFound()

        tintucs = Tintuc.search(request.website.website_domain(), order="create_date asc, id asc")

        if not tintuc and len(tintucs) == 1:
            return request.redirect('/tintuc/%s' % slug(tintucs[0]), code=302)

        date_begin, date_end, state = opt.get('date_begin'), opt.get('date_end'), opt.get('state')

        if tag and request.httprequest.method == 'GET':
            # redirect get tag-1,tag-2 -> get tag-1
            tags = tag.split(',')
            if len(tags) > 1:
                url = QueryURL('' if tintuc else '/tintuc', ['tintuc', 'tag'], tintuc=tintuc, tag=tags[0], date_begin=date_begin, date_end=date_end, search=search)()
                return request.redirect(url, code=302)

        values = self._prepare_tintuc_values(tintucs=tintucs, tintuc=tintuc, date_begin=date_begin, date_end=date_end, tags=tag, state=state, page=page, search=search)

        # in case of a redirection need by `_prepare_blog_values` we follow it
        if isinstance(values, werkzeug.wrappers.Response):
            return values

        if tintuc:
            values['main_object'] = tintuc
            values['edit_in_backend'] = True
            values['tintuc_url'] = QueryURL('', ['tintuc', 'tag'], tintuc=tintuc, tag=tag, date_begin=date_begin, date_end=date_end, search=search)
        else:
            values['tintuc_url'] = QueryURL('/tintuc', ['tag'], date_begin=date_begin, date_end=date_end, search=search)

        return request.render("website_tintuc.tintuc_post_short", values)

    @http.route(['''/tintuc/<model("tintuc.tintuc"):tintuc>/feed'''], type='http', auth="public", website=True, sitemap=True)
    def tintuc_feed(self, tintuc, limit='15', **kwargs):
        v = {}
        v['tintuc'] = tintuc
        v['base_url'] = tintuc.get_base_url()
        v['posts'] = request.env['tintuc.post'].search([('tintuc_id', '=', tintuc.id)], limit=min(int(limit), 50), order="post_date DESC")
        v['html2plaintext'] = html2plaintext
        r = request.render("website_tintuc.tintuc_feed", v, headers=[('Content-Type', 'application/atom+xml')])
        return r

    @http.route([
        '''/tintuc/<model("tintuc.tintuc"):tintuc>/post/<model("tintuc.post", "[('tintuc_id','=',tintuc.id)]"):tintuc_post>''',
    ], type='http', auth="public", website=True, sitemap=False)
    def old_tintuc_post(self, tintuc, tintuc_post, tag_id=None, page=1, enable_editor=None, **post):
        # Compatibility pre-v14
        return request.redirect(_build_url_w_params("/tintuc/%s/%s" % (slug(tintuc), slug(tintuc_post)), request.params), code=301)

    @http.route([
        '''/tintuc/<model("tintuc.tintuc"):tintuc>/<model("tintuc.post", "[('tintuc_id','=',tintuc.id)]"):tintuc_post>''',
    ], type='http', auth="public", website=True, sitemap=True)
    def tintuc_post(self, tintuc, tintuc_post, tag_id=None, page=1, enable_editor=None, **post):
        """ Prepare all values to display the tintuc.

        :return dict values: values for the templates, containing

         - 'tintuc_post': browse of the current post
         - 'tintuc': browse of the current tintuc
         - 'tintucs': list of browse records of tintucs
         - 'tag': current tag, if tag_id in parameters
         - 'tags': all tags, for tag-based navigation
         - 'pager': a pager on the comments
         - 'nav_list': a dict [year][month] for archives navigation
         - 'next_post': next tintuc post, to direct the user towards the next interesting post
        """
        TintucPost = request.env['tintuc.post']
        date_begin, date_end = post.get('date_begin'), post.get('date_end')

        domain = request.website.website_domain()
        tintucs = tintuc.search(domain, order="create_date, id asc")

        tag = None
        if tag_id:
            tag = request.env['tintuc.tag'].browse(int(tag_id))
        tintuc_url = QueryURL('', ['tintuc', 'tag'], tintuc=tintuc_post.tintuc_id, tag=tag, date_begin=date_begin, date_end=date_end)

        if not tintuc_post.tintuc_id.id == tintuc.id:
            return request.redirect("/tintuc/%s/%s" % (slug(tintuc_post.tintuc_id), slug(tintuc_post)), code=301)

        tags = request.env['tintuc.tag'].search([])

        # Find next Post
        tintuc_post_domain = [('tintuc_id', '=', tintuc.id)]
        if not request.env.user.has_group('website.group_website_designer'):
            tintuc_post_domain += [('post_date', '<=', fields.Datetime.now())]

        all_post = TintucPost.search(tintuc_post_domain)

        if tintuc_post not in all_post:
            return request.redirect("/tintuc/%s" % (slug(tintuc_post.tintuc_id)))

        # should always return at least the current post
        all_post_ids = all_post.ids
        current_tintuc_post_index = all_post_ids.index(tintuc_post.id)
        nb_posts = len(all_post_ids)
        next_post_id = all_post_ids[(current_tintuc_post_index + 1) % nb_posts] if nb_posts > 1 else None
        next_post = next_post_id and TintucPost.browse(next_post_id) or False

        values = {
            'tags': tags,
            'tag': tag,
            'tintuc': tintuc,
            'tintuc_post': tintuc_post,
            'tintucs': tintucs,
            'main_object': tintuc_post,
            'nav_list': self.nav_list(tintuc),
            'enable_editor': enable_editor,
            'next_post': next_post,
            'date': date_begin,
            'tintuc_url': tintuc_url,
        }
        response = request.render("website_tintuc.tintuc_post_complete", values)

        if tintuc_post.id not in request.session.get('posts_viewed', []):
            if sql.increment_field_skiplock(tintuc_post, 'visits'):
                if not request.session.get('posts_viewed'):
                    request.session['posts_viewed'] = []
                request.session['posts_viewed'].append(tintuc_post.id)
                request.session.modified = True
        return response

    @http.route('/tintuc/<int:tintuc_id>/post/new', type='http', auth="user", website=True)
    def tintuc_post_create(self, tintuc_id, **post):
        # Use sudo so this line prevents both editor and admin to access tintuc from another website
        # as browse() will return the record even if forbidden by security rules but editor won't
        # be able to access it
        if not request.env['tintuc.tintuc'].browse(tintuc_id).sudo().can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()

        new_tintuc_post = request.env['tintuc.post'].create({
            'tintuc_id': tintuc_id,
            'is_published': False,
        })
        return request.redirect("/tintuc/%s/%s?enable_editor=1" % (slug(new_tintuc_post.tintuc_id), slug(new_tintuc_post)))

    @http.route('/tintuc/post_duplicate', type='http', auth="user", website=True, methods=['POST'])
    def tintuc_post_copy(self, tintuc_post_id, **post):
        """ Duplicate a blog.

        :param blog_post_id: id of the blog post currently browsed.

        :return redirect to the new blog created
        """
        new_tintuc_post = request.env['tintuc.post'].with_context(mail_create_nosubscribe=True).browse(int(tintuc_post_id)).copy()
        return request.redirect("/tintuc/%s/%s?enable_editor=1" % (slug(new_tintuc_post.tintuc_id), slug(new_tintuc_post)))

    class Home(Home):
        @http.route()
        def index(self, *args, **kw):
            super(Home, self).index(*args, **kw)
            website_post_ids = request.env['tintuc.post'].search([('is_published', '=', True)])
            return request.render('website.homepage', {
                'website_post_ids': website_post_ids
            })
