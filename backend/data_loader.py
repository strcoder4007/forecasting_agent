"""Data loading module for forecasting agent."""
from pathlib import Path
from typing import Optional
import pandas as pd


class DataLoader:
    """Loads and validates data from CSV files."""

    DATA_DIR = Path(__file__).parent.parent / "data"

    # Column mappings based on PRD.md
    COLUMN_MAPPINGS = {
        "sales": {
            "store_id": "Store_ID",
            "sku_id": "SKU",
            "date": "date",
            "qty_sold": "Quantity",
            "discount_pct": "Markdown",
        },
        "stock": {
            "store_id": "LOC_ID",
            "sku_id": "SKU",
            "date": "date",
            "stock_qty": "SOH",
        },
        "items": {
            "sku_id": "SKU",
            "price": "Gross Selling Price",
        },
        "stores": {
            "store_id": "Store Id",
            "cluster_label": "Store Grade",
            "region": "County",
        },
    }

    def __init__(self):
        self.sales_df: Optional[pd.DataFrame] = None
        self.stock_df: Optional[pd.DataFrame] = None
        self.items_df: Optional[pd.DataFrame] = None
        self.stores_df: Optional[pd.DataFrame] = None
        self._validated = False

    def validate_files(self) -> dict:
        """Validate that all required data files exist and are readable."""
        warnings = []
        file_info = {}

        required_files = [
            "SALES_MASTER.xls",
            "SOH_MASTER.xls",
            "ITEM_MASTER.xls",
            "STORE_MASTER.csv",
        ]

        for filename in required_files:
            filepath = self.DATA_DIR / filename
            if not filepath.exists():
                file_info[filename] = {"status": "missing", "rows": 0}
                warnings.append(f"Missing file: {filename}")
            else:
                try:
                    # Read first few rows to get info
                    df = pd.read_csv(filepath, nrows=1000)
                    file_info[filename] = {
                        "status": "ok",
                        "rows": "estimated from file size",
                        "columns": list(df.columns),
                    }
                except Exception as e:
                    file_info[filename] = {"status": "error", "error": str(e)}
                    warnings.append(f"Error reading {filename}: {str(e)}")

        status = "ok" if not warnings else "warning"
        return {"status": status, "file_info": file_info, "warnings": warnings}

    def load_sales(self) -> pd.DataFrame:
        """Load and process sales data."""
        filepath = self.DATA_DIR / "SALES_MASTER.xls"
        df = pd.read_csv(filepath)

        # Apply column mapping
        mapping = self.COLUMN_MAPPINGS["sales"]
        df = df.rename(columns=mapping)

        # Parse date
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

        # Create combo_id
        df["combo_id"] = df["store_id"] + "_" + df["sku_id"]

        self.sales_df = df
        return df

    def load_stock(self) -> pd.DataFrame:
        """Load and process stock data."""
        filepath = self.DATA_DIR / "SOH_MASTER.xls"
        df = pd.read_csv(filepath)

        # Apply column mapping
        mapping = self.COLUMN_MAPPINGS["stock"]
        df = df.rename(columns=mapping)

        # Parse date
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

        # Create combo_id
        df["combo_id"] = df["store_id"] + "_" + df["sku_id"]

        self.stock_df = df
        return df

    def load_items(self) -> pd.DataFrame:
        """Load and process item data."""
        filepath = self.DATA_DIR / "ITEM_MASTER.xls"
        df = pd.read_csv(filepath)

        # Apply column mapping
        mapping = self.COLUMN_MAPPINGS["items"]
        df = df.rename(columns=mapping)

        self.items_df = df
        return df

    def load_stores(self) -> pd.DataFrame:
        """Load and process store data."""
        filepath = self.DATA_DIR / "STORE_MASTER.csv"
        df = pd.read_csv(filepath)

        # Apply column mapping
        mapping = self.COLUMN_MAPPINGS["stores"]
        df = df.rename(columns=mapping)

        self.stores_df = df
        return df

    def load_all(self) -> dict:
        """Load all data files."""
        return {
            "sales": self.load_sales(),
            "stock": self.load_stock(),
            "items": self.load_items(),
            "stores": self.load_stores(),
        }

    def get_price_by_sku(self) -> pd.Series:
        """Get average price per SKU."""
        if self.items_df is None:
            self.load_items()
        return self.items_df.groupby("sku_id")["price"].mean()

    def get_store_info(self) -> pd.DataFrame:
        """Get store metadata."""
        if self.stores_df is None:
            self.load_stores()
        return self.stores_df[["store_id", "cluster_label", "region"]]
