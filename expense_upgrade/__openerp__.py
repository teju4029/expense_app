{
    'name' : 'Expense',
	'version' : '0.1',
	'category' : 'expense',
	'description' : """
		This module is created to handle Expenses and also for single line refuse 
	""",
    'author': 'OpenErp4you',
    'depends': ['base_setup','hr','hr_expense', 'hr_contract','mail'],

    'data': [
          'hr_expense_view.xml',
        'sequence/sequence_view.xml',
        'hr_demo_view.xml'
    ],
    
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': True,
}