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

{
    "name": "MRP Without internal Picking",
    "version": "0.1",
    "author": "NaN Projectes de Programari Lliure S.L.",
    "category": "Production",
    "website": "http://www.nan-tic.com",
    "description": """    
To work with production orders without picking internal material collection.

Lets check the availability of materials in the same order of production, 
taking into account the supplies!

It is also possible to cancel the availability of input materials in order to 
give priority to other lines of production.
    """,
    "depends": [
        "mrp",
    ],
    "init_xml": [],
    "update_xml": [
        "workflow.xml",
        "mrp_view.xml",
    ],
    "demo_xml": [],
    "test": [
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
