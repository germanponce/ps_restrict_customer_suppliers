# -*- encoding: utf-8 -*-
# Coded by German Ponce Dominguez 
#     ▬▬▬▬▬.◙.▬▬▬▬▬  
#       ▂▄▄▓▄▄▂  
#    ◢◤█▀▀████▄▄▄▄▄▄ ◢◤  
#    █▄ █ █▄ ███▀▀▀▀▀▀▀ ╬  
#    ◥ █████ ◤  
#     ══╩══╩═  
#       ╬═╬  
#       ╬═╬ Dream big and start with something small!!!  
#       ╬═╬  
#       ╬═╬ You can do it!  
#       ╬═╬   Let's go...
#    ☻/ ╬═╬   
#   /▌  ╬═╬   
#   / \
# Cherman Seingalt - german.ponce@outlook.com

import logging
import warnings

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, ValidationError
from odoo.osv import expression
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval, time

class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    dont_show_customers = fields.Boolean(string='No mostrar Clientes')
    dont_show_suppliers = fields.Boolean(string='No mostrar Proveedores')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):

        if self.env.user.dont_show_suppliers:
            args.append(('supplier_rank', '=', 0))
            args.append(('customer_rank', '>', 0))
        if self.env.user.dont_show_customers:
            args.append(('customer_rank', '=', 0))
            args.append(('supplier_rank', '>', 0))
        res = super(ResPartner, self)._search(args, offset=offset, limit=limit,
                                                    order=order, count=count, access_rights_uid=access_rights_uid)

        return res

# class AccountMove(models.Model):
#     _inherit = 'account.move'

#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):

#         if self.env.user.journal_ids.ids:
#             args.append(('journal_id', 'in', self.env.user.journal_ids.ids))
#         res = super(AccountMove, self)._search(args, offset=offset, limit=limit,
#                                                     order=order, count=count, access_rights_uid=access_rights_uid)

#         return res


class IrRule(models.Model):
    _inherit = 'ir.rule'

    super_rule = fields.Boolean('Regla Especial', help="Funciona como una global pero con grupos.")

    @api.model
    @tools.conditional(
        'xml' not in config['dev_mode'],
        tools.ormcache('self.env.uid', 'self.env.su', 'model_name', 'mode',
                       'tuple(self._compute_domain_context_values())'),
    )
    def _compute_domain(self, model_name, mode="read"):
        rules = self._get_rules(model_name, mode=mode)
        if not rules:
            return

        # browse user and rules as SUPERUSER_ID to avoid access errors!
        eval_context = self._eval_context()
        user_groups = self.env.user.groups_id
        global_domains = []                     # list of domains
        group_domains = []                      # list of domains
        for rule in rules.sudo():
            # evaluate the domain for the current user
            dom = safe_eval(rule.domain_force, eval_context) if rule.domain_force else []
            dom = expression.normalize_domain(dom)
            if not rule.groups:
                global_domains.append(dom)
            elif rule.groups & user_groups:
                #### Cherman - Aqui hacemos la Magia - si es super regla va al inicio como global saltandose el OR ####
                if rule.super_rule:
                    global_domains.append(dom)
                else:
                    group_domains.append(dom)

        # combine global domains and group domains
        if not group_domains:
            return expression.AND(global_domains)
        return expression.AND(global_domains + [expression.OR(group_domains)])
