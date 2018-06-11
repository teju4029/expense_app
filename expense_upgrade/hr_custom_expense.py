from odoo import fields, models, api, _
from odoo import exceptions
import datetime
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class ouc_expense_custom(models.Model):
    _inherit = 'hr.expense'


    analytic_account_id = fields.Many2one('account.analytic.account',
            states={'post': [('readonly', True)], 'done': [('readonly', True)]},
            oldname='analytic_account')
    account_id = fields.Many2one('account.account', string='Account',
                                 default=lambda self: self.env['ir.property'].get('property_account_expense_categ_id',
                                                                                  'product.category'),
                                 related='product_id.property_account_expense_id',readonly="1")

    received_true=fields.Boolean(string="PR")
    refuse_details = fields.Char(string="Refuse Details")
    refuse_reason = fields.Selection(
        [('incorrect amount', 'Incorrect Amount'), ('expense not approved', 'Expense not approved'),
         ('old expense', 'Old expense'), ('duplicate claim', 'Duplicate claim'), ('incorrect bill', 'Incorrect bill')],
        string='Refuse Reason')
    c_is_approve=fields.Boolean(string="checkRefuse")
    c_is_check_id=fields.Boolean(string="refresh",compute='expense_cheeck_id')
    c_bill_attach_name = fields.Char(string='Attach a Bill')
    c_bill_attach  = fields.Binary(string='Bill attachment')


    # @api.onchange('employee_id')
    # def onchange_employee(self):
    #     if self.employee_id:
    #         self.analytic_account_id = self.employee_id.cost_centr.id

    def expense_button(self):
        if not self.refuse_reason:
            raise exceptions.ValidationError(_('Mention Refuse Reason'))
        else:
            self.sudo().message_post(_("Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") %(self.name,self.refuse_reason))
            self.sudo().write({'c_is_check_id':True,'state':'draft'})
            self.sudo().write({'sheet_id':False})
            #self.env.cr.execute("update hr_expense set sheet_id=NULL where id='%s'",(self.id,))
        return True

    @api.onchange('refuse_reason')
    def expense_check_method(self):
        if self.c_is_check_id:
            return {
            'warning': {
                    'message': 'Please SAVE the Changes before REFUSE this expense Also Refresh The Page after REFUSE'
                   }
                }
    @api.depends('refuse_reason')
    def expense_cheeck_id(self):
        for val in self:
          if val.refuse_reason:
             val.c_is_check_id =True




class ouc_expense_sheet(models.Model):
    _inherit = 'hr.expense.sheet'

    c_is_submit=fields.Boolean(string="IS Submited")
    c_submit_confirm=fields.Boolean(string="Submit Confirm")
    c_seq_number=fields.Char(string="Sequence")
    c_approval_manager=fields.Many2one('hr.employee',string="Approval Manager")
    c_phy_received=fields.Boolean(string="Physical" ,compute='expense_received',inverse='expense_check')
    physical_received=fields.Boolean(string="Physical Received All",related="c_phy_received")

    # @api.onchange('employee_id')
    # def onchange_employee(self):
    #     if self.employee_id:
    #         self.cost_centr = self.employee_id.cost_centr.id

    @api.model
    def create(self, create_values):
        seq = self.env['ir.sequence'].next_by_code('expensesequence')
        create_values["c_seq_number"] = seq
        res = super(ouc_expense_sheet, self).create(create_values)
        return res

    def save_button(self):

        template = self.env['ir.model.data'].get_object('expense_upgrade', 'example_email_template_id2')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        template = self.env['ir.model.data'].get_object('expense_upgrade', 'example_email_template_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        template = self.env['ir.model.data'].get_object('expense_upgrade', 'example_email_template_id5')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.c_is_submit=True

    @api.depends('c_phy_received')
    def expense_received(self):
        if self.expense_line_ids:
            i = 0
            count = 0
            for val in self.expense_line_ids:
                i += 1
                if val.received_true == True:
                     count += 1
            if i == count:
               self.c_phy_received = True

    @api.onchange('employee_id')
    def manager_list(self):
         group_obj = self.env["res.groups"]
         group_id = group_obj.search([('name', '=', 'Officer'), ('category_id.name', '=', 'Expenses')])
         emp_rec = []
         for rec in group_id.users:
             emp_ids = self.env["hr.employee"].search([('user_id', '=', rec.id)])
             if emp_ids:
                 emp_ids=emp_ids[0]
                 emp_rec.append(emp_ids.id)

         return {'domain':{'c_approval_manager':[('id','in',emp_rec)]}}

    @api.multi
    def action_sheet_move_create(self):
        res = super(ouc_expense_sheet, self).action_sheet_move_create()
        if not self.accounting_date:
            self.accounting_date = datetime.date.today()
        template = self.env['ir.model.data'].get_object('expense_upgrade', 'example_email_template_id3')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        return res

    @api.multi
    def approve_expense_sheets(self):
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})
        user = self.env.uid
        if self.c_approval_manager.user_id.id == user:
              template = self.env['ir.model.data'].get_object('expense_upgrade', 'example_email_template_id1')
              self.env['mail.template'].browse(template.id).send_mail(self.id)
        else:
             raise exceptions.ValidationError(_('Your are not the Approval Manager for this Request'))

    @api.multi
    def  payment_send_mail(self):
        if self.state == 'done':
            template = self.env['ir.model.data'].get_object('expense_upgrade', 'example_email_template_id4')
            self.env['mail.template'].browse(template.id).send_mail(self.id)
            self.c_submit_confirm=True

    @api.onchange('physical_received')
    def expense_check(self):
        if self.physical_received:
            for val in self.expense_line_ids:
                val.received_true = True

        else:
            for val in self.expense_line_ids:
                val.received_true= False

    @api.onchange('c_approval_manager')
    def approve_manage(self):
         if self.c_approval_manager:
             for val in self.expense_line_ids:
                 user1 = self.env.user
                 user = self.env.uid
                 group_hr_manager = self.env.ref('account.group_account_user')
                 if group_hr_manager in user1.groups_id or self.c_approval_manager.user_id.id == user:
                        val.c_is_approve = True
                 else:
                        val.c_is_approve = False






























