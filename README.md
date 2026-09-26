 # StockSense - Inventory Management System

## Project Overview

**StockSense** is a comprehensive, modular Inventory Management System (IMS) built for Odoo that replaces manual registers, Excel sheets, and scattered tracking methods with a centralized, real-time, easy-to-use inventory application.

The system provides complete control over stock operations including receipts, deliveries, internal transfers, and adjustments with a professional dashboard and audit trail.

## Problem Statement

Businesses struggle with:
- Manual inventory tracking (registers, Excel sheets)
- Scattered stock information across departments
- Lack of real-time visibility into stock levels
- Difficulty tracking stock movements
- Inventory reconciliation challenges

**StockSense solves these problems** by providing a centralized platform for all inventory operations.

## Solution

A complete Odoo module with:
- Real-time inventory dashboard with KPIs
- Multi-warehouse and multi-location support
- Complete stock movement workflows (receipt, delivery, transfer, adjustment)
- Audit trail with stock ledger
- Security groups and role-based access control
- Professional UI/UX designed for enterprise use

## Features

### 1. Authentication
- User signup/login using Odoo's native authentication
- Password reset and OTP-based recovery
- Automatic redirection to Inventory Dashboard
- Role-based access control

### 2. Inventory Dashboard
**Real-time KPIs:**
- Total Products in Stock
- Low Stock Items (1-5 units)
- Out of Stock Items (0 units)
- Pending Receipts
- Pending Deliveries
- Internal Transfers Scheduled

**Dynamic Filters:**
- By Document Type (Receipts, Delivery, Internal, Adjustments)
- By Status (Draft, Waiting, Ready, Done, Canceled)
- By Warehouse/Location
- By Product Category

**Quick Actions:**
- New Receipt
- New Delivery
- New Internal Transfer
- New Stock Adjustment
- View Stock Ledger

### 3. Product Management
- Create, update, and view products
- Product SKU/Code management
- Product categories
- Unit of Measure support
- Reordering rules and points
- Stock availability by location
- Current and initial stock tracking

### 4. Receipts (Incoming Stock)
**Workflow:** Create → Supplier → Products → Quantity → Validate → Stock Increases

- Record incoming goods from suppliers
- Automatic stock quantity increase upon validation
- Multi-line receipt support
- Supplier management integration
- Receipt history and tracking

### 5. Delivery Orders (Outgoing Stock)
**Workflow:** Create → Pick → Pack → Validate → Stock Decreases

- Record outgoing goods to customers
- Automatic stock quantity decrease upon validation
- Prevent delivery when stock unavailable
- Delivery status tracking (Draft, Ready, In Transit, Done)
- Customer management integration

### 6. Internal Transfers
- Support multi-warehouse transfers
- Location-to-location movements
- Transfer validation and tracking
- Movement history logging
- **Important:** Total company inventory remains unchanged after transfer

**Example:**
```
Before Transfer:
Warehouse A = 100 units

Transfer: 20 units to Warehouse B

After Transfer:
Warehouse A = 80 units
Warehouse B = 20 units
Total = 100 units (unchanged)
```

### 7. Stock Adjustments
**Workflow:** Product/Location → Physical Count → Calculate Difference → Update → Log

- Physical stock reconciliation
- Recorded vs. Physical count comparison
- Automatic variance calculation
- Adjustment reason tracking (Damage, Loss, Count Variance, Obsolete)
- Review and approval workflow

**Example:**
```
Recorded Stock = 50 units
Physical Count = 47 units
Variance = -3 units

After validation: Stock becomes 47 units
```

### 8. Stock Ledger / Movement History
Complete audit trail showing:
- Date/Time of each movement
- Product and SKU
- Movement Type (Receipt, Delivery, Transfer, Adjustment)
- Source Location
- Destination Location
- Quantity moved
- Reference Document
- User who performed the movement
- Status

**Filtering & Search:**
- By Product
- By Movement Type
- By Location
- By Date Range
- By Reference Document

### 9. Stock Status Indicators
Color-coded status system:
- 🟢 **Available** - More than 5 units
- 🟡 **Low Stock** - 1-5 units
- 🔴 **Unavailable** - 0 units

Supports reordering rules for automatic purchase orders.

### 10. Multi-Warehouse / Location Support
- Multiple warehouse management
- Multiple stock locations per warehouse
- Warehouse-wise stock tracking
- Location-wise stock tracking
- Seamless inter-warehouse transfers
- Native Odoo warehouse/location architecture

### 11. Smart Search & Filters
- SKU search
- Product search by name
- Category filtering
- Warehouse/Location filtering
- Document type filtering
- Status filtering
- Date range filtering
- Grouping by multiple dimensions

## Target Users

### Inventory Manager
**Can:**
- Manage all products
- Create/validate receipts
- Create/validate deliveries
- Create/validate transfers
- Perform stock adjustments
- View dashboard
- View stock ledger
- Approve adjustments
- Export reports

### Warehouse Staff
**Can:**
- View inventory
- Perform warehouse operations
- Create internal transfers
- Perform stock counts and adjustments
- Pick and shelve items
- View movement history
- View ledger (read-only)

## User Roles & Security

### Security Groups
1. **Inventory Manager** - Full access to all operations
2. **Warehouse Staff** - Limited operational access

### Record-Level Access Control
Implemented via Odoo's built-in security rules:
- Groups-based access
- Model-level permissions (CRUD)
- Record rules for data isolation

### Implemented Controls
✓ Cannot deliver unavailable stock
✓ Cannot transfer more than available
✓ Quantities must be positive
✓ Required fields validation
✓ Location/warehouse validation
✓ User permission verification

## Architecture

### Module Structure
```
stocksense/
├── __init__.py              # Module initialization
├── __manifest__.py          # Module metadata & dependencies
├── models/
│   ├── __init__.py
│   ├── stocksense_product.py        # Product model extensions
│   ├── stocksense_receipt.py        # Receipt/Incoming goods
│   ├── stocksense_delivery.py       # Delivery/Outgoing goods
│   ├── stocksense_transfer.py       # Internal transfers
│   ├── stocksense_adjustment.py     # Stock adjustments
│   └── stocksense_ledger.py         # Stock movement ledger
├── views/
│   ├── stocksense_product_view.xml       # Product views
│   ├── stocksense_receipt_view.xml       # Receipt views
│   ├── stocksense_delivery_view.xml      # Delivery views
│   ├── stocksense_transfer_view.xml      # Transfer views
│   ├── stocksense_adjustment_view.xml    # Adjustment views
│   ├── stocksense_ledger_view.xml        # Ledger views
│   ├── stocksense_dashboard_view.xml     # Dashboard
│   └── stocksense_menu.xml               # Menu & actions
├── security/
│   ├── stocksense_security.xml           # Security groups & rules
│   └── ir.model.access.csv               # Model access control
├── data/
│   └── stocksense_data.xml               # Sequences
├── demo/
│   └── stocksense_demo.xml               # Demo data
├── static/
│   └── src/
│       ├── js/
│       ├── css/
│       └── xml/
└── README.md                             # This file
```

### Data Models

#### Core Models
1. **stocksense.product.category** - Product categorization
2. **stocksense.receipt** - Incoming stock with lines
3. **stocksense.delivery** - Outgoing stock with lines
4. **stocksense.transfer** - Internal transfers with lines
5. **stocksense.adjustment** - Stock adjustments with lines
6. **stocksense.ledger** - Complete movement history

#### Supporting Models
- Extended **product.product** with StockSense fields
- Integrated with Odoo's **stock.warehouse**
- Integrated with Odoo's **stock.location**
- Integrated with Odoo's **stock.move**

### State Machines

**Receipt States:**
Draft → Confirmed → Done / Canceled → (Reset)

**Delivery States:**
Draft → Ready → In Transit → Done / Canceled → (Reset)

**Transfer States:**
Draft → Confirmed → In Transit → Done / Canceled → (Reset)

**Adjustment States:**
Draft → Reviewed → Done / Canceled → (Reset)

## Installation

### Prerequisites
- Odoo 16 or higher
- Python 3.8+
- Stock module installed

### Installation Steps

1. **Download the module:**
   ```bash
   # Extract StockSense_Odoo_Hackathon.zip
   unzip StockSense_Odoo_Hackathon.zip
   ```

2. **Place in Odoo addons directory:**
   ```bash
   cp -r stocksense /path/to/odoo/addons/
   ```

3. **Restart Odoo:**
   ```bash
   # Restart Odoo service/container
   systemctl restart odoo
   # or
   docker-compose restart odoo
   ```

4. **Activate in Odoo:**
   - Go to Apps
   - Search for "StockSense"
   - Click "Install"
   - Confirm installation

5. **Create Security Groups:**
   - Navigate to Settings → Users & Companies → Groups
   - Verify "Inventory Manager" and "Warehouse Staff" groups exist
   - Assign users to appropriate groups

6. **Configure Demo Data (Optional):**
   - Installation automatically loads demo data
   - Products, categories, warehouses are pre-configured
   - Modify as needed for your business

## Configuration

### Initial Setup

1. **Create Warehouses:**
   - Settings → Warehouses
   - Add your company's warehouse(s)

2. **Create Locations:**
   - Stock → Configuration → Locations
   - Add internal locations (shelves, racks, etc.)

3. **Create Products:**
   - StockSense → Products → All Products
   - Define SKU, category, UOM, reorder points

4. **Assign Security Groups:**
   - Users → Select user
   - Groups tab → Add "Inventory Manager" or "Warehouse Staff"

### Advanced Configuration

**Reorder Rules:**
- Navigate to product detail
- Set Reorder Point and Reorder Qty
- System alerts when stock falls below point

**Custom Categories:**
- StockSense → Products → Product Categories
- Create and manage categories
- Assign products to categories

**Warehouse Locations:**
- Configure hierarchical locations
- Example: WH-01/Shelf-A/Rack-01
- Track stock by precise location

## Usage

### Daily Workflow

#### 1. Receiving Goods
```
StockSense → Inventory Operations → Receipts
↓
"Create" button
↓
Fill: Supplier, Warehouse, Location, Products, Quantities
↓
"Confirm" button
↓
"Validate" button (increases stock)
```

#### 2. Delivering Goods
```
StockSense → Inventory Operations → Deliveries
↓
"Create" button
↓
Fill: Customer, Warehouse, Location, Products, Quantities
↓
"Confirm" button (checks stock availability)
↓
"Ship" button
↓
"Validate" button (decreases stock)
```

#### 3. Transferring Between Locations
```
StockSense → Inventory Operations → Internal Transfers
↓
"Create" button
↓
Fill: Source/Dest Warehouses, Locations, Products, Quantities
↓
"Confirm" button
↓
"Start Transfer" button
↓
"Complete" button (updates locations)
```

#### 4. Stock Reconciliation
```
StockSense → Inventory Operations → Stock Adjustments
↓
"Create" button
↓
Physical count vs. system
↓
Fill: Products, Recorded Qty, Physical Qty
↓
"Review" button
↓
"Validate" button (reconciles stock)
```

#### 5. Viewing Movement History
```
StockSense → Reports → Stock Ledger
↓
Search/Filter by:
   - Product
   - Date range
   - Movement type
   - Location
↓
View complete audit trail
```

### Dashboard Usage

The dashboard displays:
- Real-time KPI cards
- Quick action buttons
- Current operational status

**Access:** Main Odoo menu → StockSense → Dashboard

## Demo Workflow

### Included Demo Data

**Products:**
- Steel Rods (SR-001) - Raw Materials
- Office Chairs (OC-002) - Office Equipment
- Laptops (LT-003) - Electronics
- Printer Paper (PP-004) - Office Equipment
- Safety Helmets (SH-005) - Safety Equipment
- Electrical Cables (EC-006) - Raw Materials

**Categories:**
- Raw Materials
- Office Equipment
- Electronics
- Safety Equipment

**Sample Workflow:**
```
1. Receive 100 kg Steel Rods
   Stock: +100

2. Transfer 20 kg to Production Floor
   Warehouse A: -20, Production: +20
   Total: 100 (unchanged)

3. Deliver 20 kg finished goods
   Stock: -20

4. Adjust for 3 kg damage
   Stock: -3

Final Stock: 77 kg
Complete audit trail in Stock Ledger
```

## Odoo Version Support

- **Tested on:** Odoo 16, Odoo 17
- **Minimum:** Odoo 16
- **Python:** 3.8+

## Dependencies

### Core Dependencies
```xml
<depend>base</depend>        <!-- Odoo base module -->
<depend>stock</depend>       <!-- Odoo Stock/Inventory -->
<depend>sale</depend>        <!-- Sale module (for customers) -->
<depend>purchase</depend>    <!-- Purchase module (for suppliers) -->
```

### External Libraries
None - Uses only standard Odoo libraries

## Technical Implementation

### Key Features

1. **State Machines:** Proper workflow states with transitions
2. **Validation:** Comprehensive field and business rule validation
3. **Audit Trail:** Complete ledger of all movements
4. **Security:** Role-based access control and record rules
5. **Multi-tenancy:** Warehouse and location isolation
6. **Performance:** Optimized queries with proper indexing
7. **Error Handling:** User-friendly validation messages

### Database Structure

**stocksense_receipt** table:
- Standard Odoo fields (id, create_date, write_date, etc.)
- Receipt-specific fields (receipt_date, supplier_id, warehouse_id, state)
- One-to-many relationship with receipt_line_ids

**stocksense_ledger** table:
- Complete audit trail
- Indexed on product_id, movement_date, movement_type
- Computed balance field for running totals

## Future Improvements

1. **Barcode Scanning**
   - QR/Barcode integration for receiving/delivery
   - Mobile scanning interface

2. **Advanced Analytics**
   - Stock turnover analysis
   - Warehouse utilization reports
   - Seasonal demand forecasting

3. **Automated Workflows**
   - Auto-create purchase orders for low stock
   - Auto-create deliveries from sales orders
   - Email notifications for stock alerts

4. **Mobile Application**
   - Mobile app for warehouse operations
   - Offline support with sync
   - Real-time updates

5. **Integration Capabilities**
   - API for third-party systems
   - ERP integration
   - E-commerce integration

6. **Advanced Features**
   - Batch/Serial number tracking
   - Expiration date management
   - Cost allocation (FIFO, LIFO)
   - Lot tracking and traceability

## Support & Troubleshooting

### Common Issues

**Issue:** "Cannot delete in confirmed state"
- **Solution:** Cancel the document first, then reset to draft if needed

**Issue:** "Insufficient stock for delivery"
- **Solution:** Check available stock and increase if needed, or deliver partial quantity

**Issue:** "Source and destination cannot be same"
- **Solution:** Select different source and destination locations for transfers

**Issue:** Security group not working
- **Solution:** Assign user to security group, may need to logout/login or clear browser cache

### Getting Help

- Check the included documentation
- Review demo data for working examples
- Check Odoo logs for detailed error messages
- Verify user permissions and security groups

## Credits

**StockSense Development Team**
- Built for Odoo Hackathon
- Following Odoo best practices and architecture
- Enterprise-grade inventory management

## License

LGPL-3

## Conclusion

StockSense provides a complete, enterprise-ready solution for inventory management in Odoo. The modular architecture allows for easy customization and extension while maintaining data integrity and audit trails.

Designed for both Inventory Managers and Warehouse Staff, it provides the tools needed for efficient stock management in modern businesses.

---

**Version:** 1.0.0  
**Last Updated:** 2026  
**Odoo Compatibility:** 16+
