"""Safe, runnable ADK agent for GST invoice exception resolution.

The data-returning tools are local fixtures for development. Replace their bodies
with authenticated, read-only calls to your ERP and GST systems before deployment.
"""

from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools import ToolContext


THRESHOLD = 500.0
INSTRUCTION = Path(__file__).with_name("instruction.txt").read_text(encoding="utf-8")

INVOICES = {
    "INV-1001": {
        "id": "INV-1001",
        "invoice_number": "SUP-2026-104",
        "vendor_id": "V-001",
        "vendor_gstin": "27ABCDE1234F1Z5",
        "po_number": "PO-9001",
        "amount": 1200.0,
        "variance": 40.0,
        "quantity": 10,
    },
    "INV-1002": {
        "id": "INV-1002",
        "invoice_number": "SUP-2026-105",
        "vendor_id": "V-001",
        "vendor_gstin": "27ABCDE1234F1Z5",
        "po_number": "PO-9002",
        "amount": 2200.0,
        "variance": 700.0,
        "quantity": 20,
    },
    "INV-1003": {
        "id": "INV-1003",
        "invoice_number": "SUP-2026-106",
        "vendor_id": "V-002",
        "vendor_gstin": "29WRONG1234F1Z1",
        "po_number": "PO-9003",
        "amount": 800.0,
        "variance": 0.0,
        "quantity": 5,
    },
}

PURCHASE_ORDERS = {
    "PO-9001": {"po_number": "PO-9001", "amount": 1240.0, "quantity": 10, "status": "open"},
    "PO-9002": {"po_number": "PO-9002", "amount": 1500.0, "quantity": 20, "status": "open"},
    "PO-9003": {"po_number": "PO-9003", "amount": 800.0, "quantity": 5, "status": "open"},
}

GOODS_RECEIPTS = {
    "PO-9001": {"po_number": "PO-9001", "received_quantity": 10, "status": "received"},
    "PO-9002": {"po_number": "PO-9002", "received_quantity": 20, "status": "received"},
    "PO-9003": {"po_number": "PO-9003", "received_quantity": 5, "status": "received"},
}

VENDORS = {
    "V-001": {"vendor_id": "V-001", "approved_gstin": "27ABCDE1234F1Z5", "status": "active"},
    "V-002": {"vendor_id": "V-002", "approved_gstin": "29ABCDE1234F1Z1", "status": "active"},
}


def get_invoice(invoice_id: str, tool_context: ToolContext) -> dict:
    """Fetch one invoice by ID. Call this FIRST for every invoice task.

    Do not call this for purchase orders or GST returns. Returns
    {"status": "ok", "invoice": {...}} or {"status": "error", "message": str}.
    """
    invoice = INVOICES.get(invoice_id)
    if invoice is None:
        return {"status": "error", "message": f"Invoice {invoice_id} was not found."}
    tool_context.state["invoice_id"] = invoice_id
    tool_context.state["variance"] = invoice["variance"]
    tool_context.state["tool_calls"] = tool_context.state.get("tool_calls", 0) + 1
    return {"status": "ok", "invoice": invoice}


def get_purchase_order(po_number: str, tool_context: ToolContext) -> dict:
    """Fetch a purchase order when the invoice references one.

    Do not call if the invoice has no PO number. Returns an ok payload with the
    purchase order or an error payload when the PO cannot be found.
    """
    po = PURCHASE_ORDERS.get(po_number)
    if po is None:
        return {"status": "error", "message": f"Purchase order {po_number} was not found."}
    tool_context.state["tool_calls"] = tool_context.state.get("tool_calls", 0) + 1
    return {"status": "ok", "purchase_order": po}


def get_goods_receipt(po_number: str, tool_context: ToolContext) -> dict:
    """Fetch goods-receipt status only when quantity or receipt status needs checking.

    Do not call for price-only discrepancies. Returns an ok payload or an error
    payload if no goods receipt exists.
    """
    receipt = GOODS_RECEIPTS.get(po_number)
    if receipt is None:
        return {"status": "error", "message": f"No goods receipt exists for {po_number}."}
    tool_context.state["tool_calls"] = tool_context.state.get("tool_calls", 0) + 1
    return {"status": "ok", "goods_receipt": receipt}


def get_gst_return_match(invoice_number: str, vendor_gstin: str, tool_context: ToolContext) -> dict:
    """Check whether an invoice appears in the GST return using invoice number and GSTIN.

    Call only after invoice details are available; do not call without a GSTIN.
    Returns a match result or an error payload if either identifier is missing.
    """
    if not invoice_number or not vendor_gstin:
        return {"status": "error", "message": "Invoice number and vendor GSTIN are required."}
    tool_context.state["tool_calls"] = tool_context.state.get("tool_calls", 0) + 1
    return {"status": "ok", "matched": True, "invoice_number": invoice_number, "vendor_gstin": vendor_gstin}


def get_vendor_profile(vendor_id: str, tool_context: ToolContext) -> dict:
    """Fetch approved vendor identity and GSTIN when vendor verification is needed.

    Do not call for a missing vendor ID. Returns an ok payload with vendor data or
    an error payload if the vendor cannot be found.
    """
    vendor = VENDORS.get(vendor_id)
    if vendor is None:
        return {"status": "error", "message": f"Vendor {vendor_id} was not found."}
    tool_context.state["tool_calls"] = tool_context.state.get("tool_calls", 0) + 1
    return {"status": "ok", "vendor": vendor}


root_agent = Agent(
    name="gst_invoice_exception_agent",
    model="gemini-3.5-flash",
    description="Investigates GST invoice exceptions with read-only finance tools.",
    instruction=INSTRUCTION,
    tools=[get_invoice, get_purchase_order, get_goods_receipt, get_gst_return_match, get_vendor_profile],
)
