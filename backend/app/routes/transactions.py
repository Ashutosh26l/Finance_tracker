"""
Transaction API Routes — CRUD operations + CSV upload.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from app.database import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListResponse, CSVUploadResponse
)
from app.services.transaction_service import (
    create_transaction, get_transactions, update_transaction,
    delete_transaction, get_all_categories
)
import csv
import io
from datetime import datetime

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str = None,
    type: str = None,
    start_date: str = None,
    end_date: str = None,
    search: str = None,
    db=Depends(get_db),
):
    """List transactions with optional filtering and pagination."""
    result = await get_transactions(
        db, skip=skip, limit=limit,
        category=category, tx_type=type,
        start_date=start_date, end_date=end_date,
        search=search,
    )
    return result


@router.post("", response_model=TransactionResponse, status_code=201)
async def add_transaction(
    transaction: TransactionCreate,
    db=Depends(get_db),
):
    """Create a new transaction. Auto-categorizes if no category is provided."""
    data = transaction.model_dump()
    result = await create_transaction(db, data)
    return result


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def edit_transaction(
    transaction_id: str,
    transaction: TransactionUpdate,
    db=Depends(get_db),
):
    """Update an existing transaction."""
    data = transaction.model_dump(exclude_unset=True)
    result = await update_transaction(db, transaction_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result


@router.delete("/{transaction_id}")
async def remove_transaction(
    transaction_id: str,
    db=Depends(get_db),
):
    """Delete a transaction."""
    success = await delete_transaction(db, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}


@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    """
    Upload a CSV file to bulk import transactions.
    Expected columns: description, amount, type (income/expense), category (optional), date (optional)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    decoded = content.decode('utf-8')
    # Clean leading empty lines (including lines that are just commas from Excel)
    lines = decoded.splitlines()
    while lines and not lines[0].replace(',', '').strip():
        lines.pop(0)
        
    reader = csv.DictReader(lines)

    imported = 0
    failed = 0
    errors = []

    for i, row in enumerate(reader, 1):
        try:
            # Clean row dictionary handling empty keys
            clean_row = {}
            for k, v in row.items():
                if k is not None and v is not None and str(k).strip() != "":
                    clean_row[str(k).strip().lower()] = str(v).strip()
            
            if not clean_row:
                continue  # Skip empty rows

            # 1. Extract Amount
            raw_amount = None
            for k, v in clean_row.items():
                if 'amount' in k or 'value' in k or 'cost' in k or 'price' in k:
                    raw_amount = v
                    break
                    
            if raw_amount is None:
                debit = clean_row.get('debit', clean_row.get('withdrawal', ''))
                credit = clean_row.get('credit', clean_row.get('deposit', ''))
                if debit:
                    raw_amount = f"-{debit}"
                elif credit:
                    raw_amount = credit
                else:
                    raise ValueError("No amount, debit, or credit column found")
            
            if isinstance(raw_amount, str):
                raw_amount = raw_amount.replace('$', '').replace(',', '').strip()
            
            # Some files have empty amount cells
            if not raw_amount:
                raw_amount = '0'
                
            amount_val = float(raw_amount)

            # 2. Extract Description
            desc_val = ""
            for k, v in clean_row.items():
                if 'desc' in k or 'name' in k or 'payee' in k or 'merchant' in k:
                    desc_val = v
                    break
            
            if not desc_val:
                raise ValueError("Could not find Description/Name column")

            # 3. Extract Date
            date_val = None
            date_str = ""
            for k, v in clean_row.items():
                if 'date' in k or 'time' in k:
                    date_str = v
                    break
            
            if date_str:
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%y", "%d-%m-%y", "%Y-%m-%dT%H:%M:%S", 
                            "%d/%m/%Y %H:%M:%S", "%m/%d/%y", "%d/%m/%y"]:
                    try:
                        # Handling pandas 2 digit year formats like 10-12-25
                        date_val = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue

            # 4. Extract Category and Type
            category_val = None
            for k, v in clean_row.items():
                if 'category' in k or 'group' in k:
                    category_val = v if v else None
                    break

            type_val = clean_row.get('type', '').lower()
            if not type_val:
                if amount_val < 0 or clean_row.get('debit'):
                    type_val = "expense"
                else:
                    type_val = "expense"
            elif type_val not in ["income", "expense"]:
                if type_val in ["debit", "withdrawal", "payment"]:
                    type_val = "expense"
                else:
                    type_val = "income"

            data = {
                "description": desc_val,
                "amount": abs(amount_val),
                "type": type_val,
                "category": category_val,
                "notes": clean_row.get('notes', clean_row.get('memo', None)),
            }

            if date_val:
                data["date"] = date_val

            await create_transaction(db, data)
            imported += 1

        except Exception as e:
            failed += 1
            errors.append(f"Row {i}: {str(e)}")
            print(f"Row {i} Failed: {str(e)}")
            if len(errors) > 20:
                errors.append("... (truncated, too many errors)")
                break

    return {
        "imported": imported,
        "failed": failed,
        "errors": errors,
    }
