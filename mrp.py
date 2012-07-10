##############################################################################
#
# Copyright (c) 2012 NaN Projectes de Programari Lliure, S.L.
#                         All Rights Reserved.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv
import netsvc
from tools.translate import _
from datetime import datetime


class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    # mrp.production
    def action_confirm(self, cr, uid, ids):
        proc_ids = []
        move_obj = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")
        for production in self.browse(cr, uid, ids):
            if not production.product_lines:
                self.action_compute(cr, uid, [production.id])
                production = self.browse(cr, uid, [production.id])[0]
            routing_loc = None

            if (production.bom_id.routing_id and
                    production.bom_id.routing_id.location_id):
                routing_loc = production.bom_id.routing_id.location_id.id

            source = production.product_id.product_tmpl_id\
                    .property_stock_production.id
            data = {
                'name': 'PROD:' + production.name,
                'date': production.date_planned,
                'product_id': production.product_id.id,
                'product_qty': production.product_qty,
                'product_uom': production.product_uom.id,
                'product_uos_qty': (production.product_uos and
                        production.product_uos_qty or False),
                'product_uos': (production.product_uos and
                        production.product_uos.id or False),
                'location_id': source,
                'location_dest_id': production.location_dest_id.id,
                'move_dest_id': production.move_prod_id.id,
                'state': 'waiting',
                'company_id': production.company_id.id,
            }
            res_final_id = move_obj.create(cr, uid, data)

            self.write(cr, uid, [production.id], {
                        'move_created_ids': [(6, 0, [res_final_id])],
                    })
            moves = []
            for line in production.product_lines:
                if line.product_id.type in ('product', 'consu'):
                    res_dest_id = move_obj.create(cr, uid, {
                        'name': 'PROD:' + production.name,
                        'date': production.date_planned,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': (line.product_uos and
                                line.product_uos_qty or False),
                        'product_uos': (line.product_uos and
                                line.product_uos.id or False),
                        'location_id': (routing_loc or
                                production.location_src_id.id),
                        'location_dest_id': source,
                        'move_dest_id': res_final_id,
                        'state': 'waiting',
                        'company_id': production.company_id.id,
                    })
                    moves.append(res_dest_id)
                proc_vals = self._calc_procurement_vals_from_product_line(cr,
                        uid, line, res_dest_id)
                proc_id = proc_obj.create(cr, uid, proc_vals)
                wf_service.trg_validate(uid, 'procurement.order', proc_id,
                        'button_confirm', cr)
                proc_ids.append(proc_id)
            self.write(cr, uid, [production.id], {
                        'move_lines': [(6, 0, moves)],
                        'state': 'confirmed',
                    })
            message = _("Manufacturing order '%s' is scheduled for the %s.") \
                    % (
                        production.name,
                        datetime.strptime(production.date_planned,
                                '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'),
                    )
            self.log(cr, uid, production.id, message)
        return True

    # mrp.production
    def check_availability(self, cr, uid, ids, context=None):
        for prod in self.browse(cr, uid, ids):
            for move in prod.move_lines:
                if move.state != 'assigned':
                    return False
        return True

    # mrp.production
    def check_production(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        stock_move_obj = self.pool.get('stock.move')
        sm_ids = []
        for prod in self.browse(cr, uid, ids):
            for move in prod.move_lines:
                sm_ids.append( move.id )
                for procurement in move.procurements:
                        wf_service.trg_validate(uid, 'procurement.order',
                                procurement.id, 'button_restart', cr)
                        wf_service.trg_validate(uid, 'procurement.order',
                                procurement.id, 'button_check', cr)

        stock_move_obj.action_assign(cr, uid, sm_ids, context)

        if self.check_availability(cr, uid, ids, context):
            self.action_ready(cr, uid, ids)
        return True

    # mrp.production
    def action_produce(self, cr, uid, production_id, production_qty, 
            production_mode, context=None):

        res = super(mrp_production,self).action_produce(cr, uid, 
                production_id, production_qty, production_mode, context)

        production = self.browse(cr, uid, production_id, context)
        move_ids = [x.id for x in  production.move_lines]
        if move_ids:
            move_obj = self.pool.get('stock.move')
            move_obj.write(cr, uid, move_ids, {'prodlot_id':None}, context )

        return res


    # mrp.production
    def cancel_availability(self,cr, uid, ids, context):
        wf_service = netsvc.LocalService("workflow")
        stock_obj = self.pool.get('stock.move')
        procurement_obj = self.pool.get('procurement.order')
        move_line_ids = []
        procurement_ids = []
        for production in self.browse(cr, uid, ids, context):
            move_line_ids += [x.id for x in production.move_lines]
        
        procurement_ids += procurement_obj.search(cr, uid,
                [('origin_production_id','in',ids),
                 ('procure_method','=','make_to_stock')],
                context=context)

        self.write(cr, uid, ids, {'state':'confirmed'}, context=context)
        for p_id in ids:
            wf_service.trg_validate(uid, 'mrp.production', p_id, 
                    'action_cancel', cr)
            wf_service.trg_delete(uid, 'mrp.production', p_id, cr)
            wf_service.trg_create(uid, 'mrp.production', p_id, cr)


        stock_obj.write(cr, uid, move_line_ids, {'state':'confirmed'}, 
                context)

        procurement_obj.write(cr, uid, procurement_ids, {
            'state':'draft'}, context=context)

        for proc in self.browse(cr, uid, procurement_ids, context=context):
            wf_service.trg_delete(uid, 'procurement.order', proc.id, cr)
            wf_service.trg_create(uid, 'procurement.order', proc.id, cr)
            wf_service.trg_validate(uid, 'procurement.order', 
                    proc.id, 'button_confirm', cr )

        return True

    # mrp.production
    def force_production(self, cr, uid, ids, *args):
        """ Assigns products.
        @param *args: Arguments
        @return: True
        """
        move_ids = []
        for prod in self.browse(cr, uid, ids):
            move_ids += [x.id for x in prod.move_lines
                    if x.state in ('confirmed', 'waiting')]

        self.pool.get('stock.move').force_assign(cr, uid, move_ids)
        self.action_ready(cr, uid, ids)
        return True
mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
