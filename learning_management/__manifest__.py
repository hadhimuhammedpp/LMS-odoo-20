# -*- coding: utf-8 -*-
{
    'name': 'Learning Management Software',
    'summary': 'LMS by ABC Learning Academy',
    'version': '20.0.0.0.0',
    'description': "This is a Learning Management Software for ABC Learning Academy",
    'depends': ['base', 'sale', 'mail','contacts'],
    'sequence': 0,
    'application': True,
    'installable': True,
    'category': 'Education',
    'data': [
        'security/ir.access.csv',
        'views/lms_students_view.xml',
        'data/sequence.xml',
        'data/product_data.xml',
        'views/lms_scholarship_views.xml',
        'views/lms_enrollment_views.xml',
        'views/lms_batch_views.xml',
        'views/lms_menus.xml'
    ]
}
