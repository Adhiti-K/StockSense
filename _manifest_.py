{
    'name': 'StockSense - Inventory Management System',
    'version': '1.0.0',
    'category': 'Inventory',
    'summary': 'Modular Inventory Management System - Digitize stock operations',
    'description': '''
        StockSense is a comprehensive Inventory Management System that replaces manual registers,
        Excel sheets, and scattered tracking with a centralized, real-time application.
        
        Features:
        - Multi-warehouse and location support
        - Receipt, Delivery, Internal Transfer, and Stock Adjustment workflows
        - Real-time inventory dashboard with KPIs
        - Stock ledger and movement history tracking
        - Product management with categories and SKU
        - Security groups for Inventory Managers and Warehouse Staff
        - Smart search and filtering capabilities
    ''',
    'author': 'StockSense Team',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
        'sale',
        'purchase',
    ],
    'data': [
        # Security
        'security/stocksense_security.xml',
        'security/ir.model.access.csv',
        
        # Data & Demo
        'data/stocksense_data.xml',
        'demo/stocksense_demo.xml',
        
        # Views
        'views/stocksense_product_view.xml',
        'views/stocksense_receipt_view.xml',
        'views/stocksense_delivery_view.xml',
        'views/stocksense_transfer_view.xml',
        'views/stocksense_adjustment_view.xml',
        'views/stocksense_ledger_view.xml',
        'views/stocksense_dashboard_view.xml',
        'views/stocksense_menu.xml',
    ],
    'static': {
        'description': 'Static assets included in module',
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
